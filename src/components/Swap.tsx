"use client";

/**
 * Swap Component
 * Handles token swapping functionality with 0x Protocol integration.
 * Features:
 * - Real-time price fetching
 * - Token balance display
 * - Transaction execution and monitoring
 * - Success/failure notifications
 * - Affiliate fee handling
 */

import { useEffect, useState, useCallback } from "react";
import {
  useAccount,
  useSendTransaction,
  useWaitForTransactionReceipt,
  useBalance,
  useSignTypedData,
} from "wagmi";
import {
  parseUnits,
  formatUnits,
  type BaseError,
  Hex,
  numberToHex,
  size,
  concat,
} from "viem";
import { Loader2 } from "lucide-react";
import { Button } from "~/components/ui/button";
import { Card, CardContent } from "~/components/ui/card";
import { Input } from "~/components/ui/input";
import qs from "qs";
import { useTokenBalance } from "~/hooks/useTokenBalance";
import { QuoteResponse } from "~/lib/types/zeroex";
import { base } from "viem/chains";
import { useFrameSDK } from "~/hooks/useFrameSDK";

/**
 * Token interface defining the structure of tradeable tokens
 */
interface Token {
  symbol: string;
  name: string;
  image: string;
  address: string;
  decimals: number;
}

const ETH: Token = {
  symbol: "ETH",
  name: "Ethereum",
  image: "https://assets.coingecko.com/coins/images/279/small/ethereum.png",
  address: "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
  decimals: 18,
};

const USDC: Token = {
  symbol: "USDC",
  name: "USD Coin",
  image: "https://assets.coingecko.com/coins/images/6319/small/usdc.png",
  address: "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
  decimals: 6,
};

/**
 * Swap configuration constants
 */
const AFFILIATE_FEE = 0;
const YOUR_ADDRESS = "0x6b512f25976a164c922cb4f3ecdbb02e223ea445";

/**
 * Props for the Swap component
 */
interface SwapProps {
  setTransactionState?: (state: string) => void;
  showPercentages?: boolean;
}

const formatBalance = (
  value: number | string | undefined,
  decimals: number = 5,
): string => {
  if (!value) return "0.00000";

  const numValue = typeof value === "string" ? Number(value) : value;

  return numValue.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

/**
 * Swap Component
 * Provides the main swap interface for trading ETH to NATIVE tokens
 * Features:
 * - Real-time price updates
 * - Balance checking
 * - Transaction execution
 * - Success notifications
 * - Error handling
 * @param {SwapProps} props - Component props
 * @returns {JSX.Element} The swap interface
 */
export default function Swap({
  setTransactionState,
  showPercentages = false,
}: SwapProps) {
  const { isSDKLoaded } = useFrameSDK();

  // const [isSelling, setIsSelling] = useState(false);
  const isSelling = false;
  const sellToken = isSelling ? ETH : USDC;
  const buyToken = isSelling ? USDC : ETH;
  const [sellAmount, setSellAmount] = useState("");
  const [buyAmount, setBuyAmount] = useState("");
  const [quote, setQuote] = useState<QuoteResponse>();
  const [fetchPriceError, setFetchPriceError] = useState<string[]>([]);
  const { address, isConnected } = useAccount();
  const { data: ethBalance } = useBalance({ address });
  const { balance: tokenBalance } = useTokenBalance(address, USDC.address);
  const parsedSellAmount = sellAmount
    ? parseUnits(sellAmount, sellToken.decimals).toString()
    : undefined;
  const parsedBuyAmount = buyAmount
    ? parseUnits(buyAmount, buyToken.decimals).toString()
    : undefined;
  const [isPriceLoading, setIsPriceLoading] = useState(false);

  const {
    data: hash,
    isPending,
    error,
    sendTransaction,
  } = useSendTransaction();
  const { isLoading: isConfirming, isSuccess: isConfirmed } =
    useWaitForTransactionReceipt({
      hash,
    });

  const fetchPrice = useCallback(
    async (params: unknown) => {
      setIsPriceLoading(true);
      try {
        const response = await fetch(`/api/tokenPrice?${qs.stringify(params)}`);
        const data = await response.json();

        if (data?.validationErrors?.length > 0) {
          setFetchPriceError(data.validationErrors);
        } else {
          setFetchPriceError([]);
        }

        if (data.buyAmount) {
          setBuyAmount(formatUnits(data.buyAmount, buyToken.decimals));
        }
      } finally {
        setIsPriceLoading(false);
      }
    },
    [buyToken.decimals],
  );

  // const linkToBaseScan = useCallback((hash?: string) => {
  //   if (hash) {
  //     sdk.actions.openUrl(`https://basescan.org/tx/${hash}`);
  //   }
  // }, []);

  const fetchQuote = useCallback(
    async (params: unknown) => {
      setIsPriceLoading(true);
      try {
        const response = await fetch(`/api/tokenQuote?${qs.stringify(params)}`);
        const data = await response.json();
        // console.log("tokenQuote", data);
        setQuote(data);
      } finally {
        setIsPriceLoading(false);
        fetchPrice(params);
      }
    },
    [fetchPrice],
  );
  const { signTypedDataAsync } = useSignTypedData();

  const executeSwap = useCallback(async () => {
    console.log("executeSwap", quote?.transaction);
    if (quote) {
      setTransactionState?.("loading");
      if (quote.permit2?.eip712) {
        let signature: Hex | undefined;
        try {
          signature = await signTypedDataAsync(quote.permit2.eip712);
          console.log("Signed permit2 message from quote response");
        } catch (error) {
          console.error("Error signing permit2 coupon:", error);
        }

        // (2) Append signature length and signature data to calldata

        if (signature && quote?.transaction?.data) {
          const signatureLengthInHex = numberToHex(size(signature), {
            signed: false,
            size: 32,
          });

          const transactionData = quote.transaction.data as Hex;
          const sigLengthHex = signatureLengthInHex as Hex;
          const sig = signature as Hex;

          quote.transaction.data = concat([transactionData, sigLengthHex, sig]);
        } else {
          throw new Error("Failed to obtain signature or transaction data");
        }
      }

      // (3) Submit the transaction with Permit2 signature

      if (sendTransaction) {
        sendTransaction({
          // account: walletClient?.account.address,
          gas: !!quote?.transaction.gas
            ? BigInt(quote?.transaction.gas)
            : undefined,
          to: quote?.transaction.to,
          data: quote.transaction.data, // submit
          value: quote?.transaction.value
            ? BigInt(quote.transaction.value)
            : undefined, // value is used for native tokens
        });
      }

      // sendTransaction({
      //   gas: quote.transaction.gas ? BigInt(quote.transaction.gas) : undefined,
      //   to: quote.transaction.to,
      //   data: quote.transaction.data,
      //   value: BigInt(quote.transaction.value),
      // });
    }
  }, [quote, sendTransaction, setTransactionState, signTypedDataAsync]);

  // const handleSwapTokens = useCallback(() => {
  //   setIsSelling(!isSelling);
  //   setSellAmount("");
  //   setBuyAmount("");
  //   setQuote(undefined);
  //   setFetchPriceError([]);
  // }, [isSelling]);

  const handlePercentageClick = useCallback(
    (percentage: number) => {
      const balance = isSelling
        ? tokenBalance?.balance_formatted
        : ethBalance?.value
          ? formatUnits(ethBalance.value, 18)
          : "0";

      if (balance) {
        const amount = (Number(balance) * percentage).toFixed(6);
        setSellAmount(amount);
      }
    },
    [isSelling, tokenBalance, ethBalance],
  );

  useEffect(() => {
    if (isConfirmed) {
      setTransactionState?.("success");
    } else if (error) {
      setTransactionState?.("error");
    }
  }, [isConfirmed, error, setTransactionState]);

  useEffect(() => {
    const params = {
      chainId: base.id,
      sellToken: sellToken.address,
      buyToken: buyToken.address,
      sellAmount: parsedSellAmount,
      buyAmount: parsedBuyAmount,
      taker: address,
      swapFeeRecipient: YOUR_ADDRESS,
      swapFeeBps: AFFILIATE_FEE,
      swapFeeToken: buyToken.address,
      tradeSurplusRecipient: address,
    };

    const timeoutId = setTimeout(() => {
      if (sellAmount !== "") {
        fetchQuote(params);
        fetchPrice(params);
      }
    }, 1000);

    return () => clearTimeout(timeoutId);
  }, [
    address,
    buyAmount,
    buyToken.address,
    parsedBuyAmount,
    parsedSellAmount,
    sellAmount,
    sellToken.address,
    fetchPrice,
    fetchQuote,
  ]);

  if (!isSDKLoaded) {
    return (
      <div className="flex items-center justify-center min-h-full">
        <Loader2 className="w-8 h-8 animate-spin text-stone-500" />
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-full">
      <Card className="w-full max-w-md shadow-lg">
        <CardContent className="pt-6 px-6 pb-4 space-y-4">
          {/* Input Token */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-gray-600 font-mono text-xs uppercase mx-1">
              <span>
                Balance:{" "}
                {isSelling
                  ? formatBalance(
                      ethBalance?.value
                        ? formatUnits(ethBalance.value, 18)
                        : "0",
                    )
                  : formatBalance(tokenBalance?.balance_formatted)}{" "}
                {sellToken.symbol}
              </span>
            </div>
            <div className="flex items-center space-x-2 p-2 bg-stone-50 text-gray-800 rounded-lg">
              <div className="flex items-center space-x-2 pl-1 pr-3 py-1 h-10 rounded-lg border">
                <img
                  src={sellToken.image}
                  width={24}
                  height={24}
                  className="w-6 h-6 rounded-full"
                  alt={`${sellToken.symbol} logo`}
                />
                <span className="text-sm font-medium">{sellToken.symbol}</span>
              </div>
              <Input
                type="number"
                value={sellAmount}
                onChange={(e) => setSellAmount(e.target.value)}
                className="h-10 flex-1 bg-white text-right text-base"
                placeholder="0.0"
              />
            </div>
            {/* Percentage Buttons */}
            {showPercentages && (
              <div className="flex gap-2 mt-2">
                {[0.25, 0.5, 0.75, 1].map((percentage) => (
                  <Button
                    key={`percentage-${percentage}`}
                    variant="outline"
                    size="sm"
                    onClick={() => handlePercentageClick(percentage)}
                    className="flex-1 text-xs rounded-full hover:-rotate-2 hover:bg-emerald-600 hover:text-white hover:scale-105 active:scale-95 active:shadow-inner font-mono uppercase"
                  >
                    {percentage * 100}%
                  </Button>
                ))}
              </div>
            )}
          </div>

          {/* Swap Direction Button */}
          {/* <div className="flex justify-center py-2">
            <div className="h-px bg-stone-200 w-36 my-2" />
            <Button
              variant="ghost"
              size="icon"
              onClick={handleSwapTokens}
              className="bg-white shadow-md rounded-full h-8 w-8 z-10 transition-all duration-200 hover:bg-emerald-600 hover:text-white font-bold rotate-90 active:duration-300 active:rotate-180"
            >
              <RiSwapBoxLine className="h-6 w-6" />
            </Button>
          </div> */}

          {/* Output Token */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-stone-600 font-mono text-xs uppercase mx-1">
              <span>
                1 {buyToken.symbol} ≈{" "}
                {quote &&
                Number(quote.buyAmount) > 0 &&
                Number(quote.sellAmount) > 0
                  ? formatBalance(
                      Number(
                        formatUnits(
                          BigInt(quote.sellAmount),
                          sellToken.decimals,
                        ),
                      ) /
                        Number(
                          formatUnits(
                            BigInt(quote.buyAmount),
                            buyToken.decimals,
                          ),
                        ),
                      0,
                    )
                  : "0.0"}{" "}
                {sellToken.symbol}
              </span>
            </div>
            <div className="flex items-center space-x-2 p-2 bg-stone-50 text-gray-800 rounded-lg">
              <div className="flex items-center space-x-2 bg-white pl-1 pr-3 py-1 h-10 rounded-lg border">
                <img
                  src={buyToken.image}
                  width={24}
                  height={24}
                  className="w-6 h-6 rounded-full"
                  alt={`${buyToken.symbol} logo`}
                />
                <span className="text-sm font-medium">{buyToken.symbol}</span>
              </div>
              <Input
                type="text"
                min={0}
                value={
                  isPriceLoading && buyAmount === "" ? "Loading..." : buyAmount
                }
                className="h-10 flex-1 text-gray-500 bg-white text-right text-base pr-4"
                readOnly
              />
            </div>
          </div>

          {/* Error Messages */}
          {fetchPriceError.length > 0 && (
            <div className="text-rose-600 text-center text-sm p-2 bg-rose-50 rounded-xl">
              {fetchPriceError.map((error, index) => (
                <div key={`priceError-${index}`}>
                  {error.replace("Error: ", "")}
                </div>
              ))}
            </div>
          )}
          {error && (
            <div className="relative flex items-baseline gap-2 text-rose-600 text-center text-sm p-2 bg-rose-50 rounded-xl">
              <span className="font-mono text-xs text-rose-200 uppercase">
                Error
              </span>
              <div className="flex text-center w-full">
                {(error as BaseError).shortMessage.replace("Error: ", "") ||
                  error.message.replace("Error: ", "")}
              </div>
            </div>
          )}

          <Button
            size="lg"
            className="w-full uppercase text-sm shadow-md"
            onClick={executeSwap}
            disabled={
              !isConnected ||
              !sellAmount ||
              !buyAmount ||
              isPending ||
              isConfirming
            }
          >
            {!isConnected ? (
              "Connect Wallet"
            ) : isPending || isConfirming ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
                Processing...
              </>
            ) : (
              "Swap to ETH"
            )}
          </Button>

          <div className="h-4 flex items-center justify-center text-xs text-stone-500 text-center">
            {quote && Number(quote.minBuyAmount) > 0
              ? `Minimum received:${" "} ${formatBalance(
                  formatUnits(BigInt(quote.minBuyAmount), buyToken.decimals),
                )} ${buyToken.symbol}`
              : " "}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
