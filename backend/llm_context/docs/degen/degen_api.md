Degen API
Developers wanting to build on top of Degen can utilize the following public APIs.

The <season> path variable can be set to: current, season1, season2, etc.

The <wallet> path variable is optional, omitting it will return a full list of results by default.

Use limit to specify the number of records and offset to set the starting point.

The <cast_hash> path variable for casts must be formatted as \x795ea3a46873e5b9e8a1cd7cb9734bbc6ad62c89.

Airdrop 1
GETapi.degen.tips/airdrop1/claims?wallet=<wallet>
GETapi.degen.tips/airdrop1/points?wallet=<wallet>
Airdrop 2
GETapi.degen.tips/airdrop2/<season>/points?fid=<fid>
GETapi.degen.tips/airdrop2/<season>/points?wallet=<wallet>
GETapi.degen.tips/airdrop2/allowances?fid=<fid>
GETapi.degen.tips/airdrop2/allowances?wallet=<wallet>
GETapi.degen.tips/airdrop2/tips?fid=<fid>
GETapi.degen.tips/airdrop2/tips?hash=<cast_hash>
Liquidity Mining
GETapi.degen.tips/liquidity-mining/<season>/points?fid=<fid>
GETapi.degen.tips/liquidity-mining/<season>/points?wallet=<wallet>
Raindrops
GETapi.degen.tips/raindrop/<season>/points?fid=<fid>
GETapi.degen.tips/raindrop/<season>/points?wallet=<wallet>
GETapi.degen.tips/raindrop/casts

{
"info": {
"\_postman_id": "4c0ab844-d23a-4e3c-a044-42832d3f8917",
"name": "Degen.tips APIs",
"schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
"\_exporter_id": "16125606"
},
"item": [
{
"name": "Airdrop 1 Claims",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop1/claims?limit=100&offset=0&wallet=0xf1E7DBEDD9e06447e2F99B1310c09287b734addc",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop1",
"claims"
],
"query": [
{
"key": "limit",
"value": "100"
},
{
"key": "offset",
"value": "0"
},
{
"key": "wallet",
"value": "0xf1E7DBEDD9e06447e2F99B1310c09287b734addc"
}
]
}
},
"response": []
},
{
"name": "Airdrop 1 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop1/points?limit=100&offset=0&wallet=0xf1E7DBEDD9e06447e2F99B1310c09287b734addc",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop1",
"points"
],
"query": [
{
"key": "limit",
"value": "100"
},
{
"key": "offset",
"value": "0"
},
{
"key": "wallet",
"value": "0xf1E7DBEDD9e06447e2F99B1310c09287b734addc"
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Tip Allowances",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/allowances?fid=234616",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"allowances"
],
"query": [
{
"key": "wallet",
"value": "0xf1E7DBEDD9e06447e2F99B1310c09287b734addc",
"disabled": true
},
{
"key": "limit",
"value": "1",
"disabled": true
},
{
"key": "offset",
"value": "1",
"disabled": true
},
{
"key": "fid",
"value": "234616"
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Tips",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/tips?hash=\\x795ea3a46873e5b9e8a1cd7cb9734bbc6ad62c89",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"tips"
],
"query": [
{
"key": "limit",
"value": "10",
"disabled": true
},
{
"key": "fid",
"value": "15983",
"disabled": true
},
{
"key": "offset",
"value": "0",
"disabled": true
},
{
"key": "hash",
"value": "\\x795ea3a46873e5b9e8a1cd7cb9734bbc6ad62c89"
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Current Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/current/points?limit=50&wallet=0x19d8da2674e8a025154153297ea3ab918debf96d",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"current",
"points"
],
"query": [
{
"key": "limit",
"value": "50"
},
{
"key": "wallet",
"value": "0x19d8da2674e8a025154153297ea3ab918debf96d"
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Season 1 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/season1/points?limit=50",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"season1",
"points"
],
"query": [
{
"key": "limit",
"value": "50"
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Season 2 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/season2/points?limit=50",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"season2",
"points"
],
"query": [
{
"key": "limit",
"value": "50"
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Season 3 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/season3/points?limit=50",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"season3",
"points"
],
"query": [
{
"key": "limit",
"value": "50"
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Season 4 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/season4/points?limit=50",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"season4",
"points"
],
"query": [
{
"key": "limit",
"value": "50"
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Season 5 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/season5/points?limit=50&wallet=0xf1e7dbedd9e06447e2f99b1310c09287b734addc",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"season5",
"points"
],
"query": [
{
"key": "limit",
"value": "50"
},
{
"key": "wallet",
"value": "0xf1e7dbedd9e06447e2f99b1310c09287b734addc"
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Season 5 Merkle Proofs",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/season5/merkleproofs?wallet=0x495d4d2203be7775d22ee8f84017544331300d09",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"season5",
"merkleproofs"
],
"query": [
{
"key": "wallet",
"value": "0x495d4d2203be7775d22ee8f84017544331300d09"
},
{
"key": "limit",
"value": "50",
"disabled": true
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Season 6 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/season6/points?wallet=0xd5a589b294b4a1687554faf18572640e6024efe4",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"season6",
"points"
],
"query": [
{
"key": "limit",
"value": "50",
"disabled": true
},
{
"key": "wallet",
"value": "0xd5a589b294b4a1687554faf18572640e6024efe4"
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Season 6 Merkle Proofs",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/season6/merkleproofs?wallet=0x495d4D2203Be7775D22Ee8F84017544331300d09",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"season6",
"merkleproofs"
],
"query": [
{
"key": "wallet",
"value": "0x495d4D2203Be7775D22Ee8F84017544331300d09"
},
{
"key": "limit",
"value": "50",
"disabled": true
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Season 7 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/season7/points?wallet=0xbfAc9261628e3e27440328Cbc341c1dbc32462B0",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"season7",
"points"
],
"query": [
{
"key": "limit",
"value": "50",
"disabled": true
},
{
"key": "wallet",
"value": "0xbfAc9261628e3e27440328Cbc341c1dbc32462B0"
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Season 7 Merkle Proofs",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/season7/merkleproofs?wallet=0xbfAc9261628e3e27440328Cbc341c1dbc32462B0",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"season7",
"merkleproofs"
],
"query": [
{
"key": "wallet",
"value": "0xbfAc9261628e3e27440328Cbc341c1dbc32462B0"
},
{
"key": "limit",
"value": "50",
"disabled": true
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Season 8 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/season8/points?wallet=0x495d4D2203Be7775D22Ee8F84017544331300d09",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"season8",
"points"
],
"query": [
{
"key": "limit",
"value": "50",
"disabled": true
},
{
"key": "wallet",
"value": "0x495d4D2203Be7775D22Ee8F84017544331300d09"
}
]
}
},
"response": []
},
{
"name": "Airdrop 2 Season 8 Merkle Proofs",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/airdrop2/season8/merkleproofs?wallet=0x041a43bb9848aff9ae7823398af88e1d2b2aad3f",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"airdrop2",
"season8",
"merkleproofs"
],
"query": [
{
"key": "wallet",
"value": "0x041a43bb9848aff9ae7823398af88e1d2b2aad3f"
},
{
"key": "limit",
"value": "50",
"disabled": true
}
]
}
},
"response": []
},
{
"name": "Airdrop Raindrop Current Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/raindrop/current/points?limit=50",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"raindrop",
"current",
"points"
],
"query": [
{
"key": "limit",
"value": "50"
}
]
}
},
"response": []
},
{
"name": "Airdrop Raindrop Season 1 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/raindrop/season1/points?limit=50&wallet=0x2cae0ac9a7a7048516868aad672c49ab632b38c8",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"raindrop",
"season1",
"points"
],
"query": [
{
"key": "limit",
"value": "50"
},
{
"key": "wallet",
"value": "0x2cae0ac9a7a7048516868aad672c49ab632b38c8"
}
]
}
},
"response": []
},
{
"name": "Airdrop Raindrop Season 1 Merkle Proofs",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/raindrop/season1/merkleproofs?wallet=0x495d4D2203Be7775D22Ee8F84017544331300d09",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"raindrop",
"season1",
"merkleproofs"
],
"query": [
{
"key": "wallet",
"value": "0x495d4D2203Be7775D22Ee8F84017544331300d09"
},
{
"key": "limit",
"value": "50",
"disabled": true
}
]
}
},
"response": []
},
{
"name": "Airdrop Raindrop Season 2 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/raindrop/season2/points?limit=50",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"raindrop",
"season2",
"points"
],
"query": [
{
"key": "limit",
"value": "50"
}
]
}
},
"response": []
},
{
"name": "Airdrop Raindrop Season 2 Merkle Proofs",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/raindrop/season2/merkleproofs?wallet=0x495d4D2203Be7775D22Ee8F84017544331300d09",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"raindrop",
"season2",
"merkleproofs"
],
"query": [
{
"key": "wallet",
"value": "0x495d4D2203Be7775D22Ee8F84017544331300d09"
},
{
"key": "limit",
"value": "50",
"disabled": true
}
]
}
},
"response": []
},
{
"name": "Liquidity Mining Season Current Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/liquidity-mining/current/points?limit=50",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"liquidity-mining",
"current",
"points"
],
"query": [
{
"key": "limit",
"value": "50"
},
{
"key": "wallet",
"value": "0xf1E7DBEDD9e06447e2F99B1310c09287b734addc",
"disabled": true
}
]
}
},
"response": []
},
{
"name": "Liquidity Mining Season 1 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/liquidity-mining/season1/points?wallet=0xf1E7DBEDD9e06447e2F99B1310c09287b734addc",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"liquidity-mining",
"season1",
"points"
],
"query": [
{
"key": "limit",
"value": "50",
"disabled": true
},
{
"key": "wallet",
"value": "0xf1E7DBEDD9e06447e2F99B1310c09287b734addc"
}
]
}
},
"response": []
},
{
"name": "Liquidity Mining Season 2 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/liquidity-mining/season2/points?wallet=0xf1E7DBEDD9e06447e2F99B1310c09287b734addc",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"liquidity-mining",
"season2",
"points"
],
"query": [
{
"key": "limit",
"value": "50",
"disabled": true
},
{
"key": "wallet",
"value": "0xf1E7DBEDD9e06447e2F99B1310c09287b734addc"
}
]
}
},
"response": []
},
{
"name": "Liquidity Mining Season 3 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/liquidity-mining/season3/points?wallet=0xf1E7DBEDD9e06447e2F99B1310c09287b734addc",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"liquidity-mining",
"season3",
"points"
],
"query": [
{
"key": "limit",
"value": "50",
"disabled": true
},
{
"key": "wallet",
"value": "0xf1E7DBEDD9e06447e2F99B1310c09287b734addc"
}
]
}
},
"response": []
},
{
"name": "Liquidity Mining Season 4 Merkle Proofs",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/liquidity-mining/season4/merkleproofs?wallet=0xf1E7DBEDD9e06447e2F99B1310c09287b734addc",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"liquidity-mining",
"season4",
"merkleproofs"
],
"query": [
{
"key": "wallet",
"value": "0xf1E7DBEDD9e06447e2F99B1310c09287b734addc"
},
{
"key": "limit",
"value": "50",
"disabled": true
}
]
}
},
"response": []
},
{
"name": "Liquidity Mining Season 4 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/liquidity-mining/season4/points?limit=50",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"liquidity-mining",
"season4",
"points"
],
"query": [
{
"key": "limit",
"value": "50"
}
]
}
},
"response": []
},
{
"name": "Liquidity Mining Season 5 Merkle Proofs",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/liquidity-mining/season5/merkleproofs?wallet=0xf1E7DBEDD9e06447e2F99B1310c09287b734addc",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"liquidity-mining",
"season5",
"merkleproofs"
],
"query": [
{
"key": "wallet",
"value": "0xf1E7DBEDD9e06447e2F99B1310c09287b734addc"
},
{
"key": "limit",
"value": "50",
"disabled": true
}
]
}
},
"response": []
},
{
"name": "Liquidity Mining Season 5 Points",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/liquidity-mining/season5/points?limit=50&wallet=0xf1E7DBEDD9e06447e2F99B1310c09287b734addc",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"liquidity-mining",
"season5",
"points"
],
"query": [
{
"key": "limit",
"value": "50"
},
{
"key": "wallet",
"value": "0xf1E7DBEDD9e06447e2F99B1310c09287b734addc"
}
]
}
},
"response": []
},
{
"name": "Farcaster Wallets",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/farcaster/wallets?wallet=0xf1E7DBEDD9e06447e2F99B1310c09287b734addc",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"farcaster",
"wallets"
],
"query": [
{
"key": "wallet",
"value": "0xf1E7DBEDD9e06447e2F99B1310c09287b734addc"
},
{
"key": "limit",
"value": "5",
"disabled": true
},
{
"key": "offset",
"value": "5",
"disabled": true
}
]
}
},
"response": []
},
{
"name": "Farcaster Tokenomics",
"request": {
"method": "GET",
"header": [],
"url": {
"raw": "https://api.degen.tips/tokenomics?category=Liquidity Mining",
"protocol": "https",
"host": [
"api",
"degen",
"tips"
],
"path": [
"tokenomics"
],
"query": [
{
"key": "category",
"value": "Liquidity Mining"
}
]
}
},
"response": []
}
]
}
