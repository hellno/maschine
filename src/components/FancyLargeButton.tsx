const FancyLargeButton = ({
    text,
    onClick,
}: {
    text: string;
    onClick?: () => void;
}) => {
  return (
    <button
      onClick={onClick}
      className="relative inline-flex h-20 overflow-hidden rounded-full p-[1px] focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 focus:ring-offset-slate-50 disabled:opacity-75 disabled:cursor-not-allowed transition-opacity"
    >
      <span className="absolute inset-[-1000%] animate-[spin_3s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#E2CBFF_0%,#393BB2_50%,#E2CBFF_100%)]" />
      <span className="inline-flex h-full w-full items-center justify-center rounded-full bg-slate-950 px-8 py-2 text-xl font-medium text-white backdrop-blur-3xl">
        {text}
      </span>
    </button>
  );
};

export default FancyLargeButton;
