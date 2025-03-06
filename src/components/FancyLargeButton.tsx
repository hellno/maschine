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
      className="relative inline-flex h-16 overflow-hidden rounded-full p-[1px] focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 focus:ring-offset-slate-50 disabled:opacity-75 disabled:cursor-not-allowed transition-opacity"
    >
      <span className="absolute inset-[-500%] animate-[spin_3s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#6366f1_0%,#3b82f6_50%,#6366f1_100%)] dark:bg-[conic-gradient(from_90deg_at_50%_50%,#E2CBFF_0%,#393BB2_50%,#E2CBFF_100%)] hover:animate-[spin_5s_linear_infinite] border-2" />
      <span className="inline-flex h-full w-full items-center justify-center rounded-full bg-white/90 px-6 py-2 text-xl font-medium text-slate-900 backdrop-blur-3xl hover:bg-slate-50 dark:bg-slate-950 dark:text-white dark:hover:bg-slate-900">
        {text}
      </span>
    </button>
  );
};

export default FancyLargeButton;
