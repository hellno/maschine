const FancyLargeButton = ({
  text,
  onClick,
}: {
  text: string;
  onClick?: () => void;
}) => {
  // ai! this button looks great on a dark background, can you add a better color that shows the border animation nicely also on a white background
  // can use dark: tailwindcss to make it work on dark mode
  return (
    <button
      onClick={onClick}
      className="relative inline-flex h-16 overflow-hidden rounded-full p-[1px] focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 focus:ring-offset-slate-50 disabled:opacity-75 disabled:cursor-not-allowed transition-opacity"
    >
      <span className="absolute inset-[-500%] animate-[spin_3s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#E2CBFF_0%,#393BB2_50%,#E2CBFF_100%)] hover:animate-[spin_5s_linear_infinite] border-2" />
      <span className="inline-flex h-full w-full items-center justify-center rounded-full bg-slate-950 px-6 py-2 text-xl font-medium text-white backdrop-blur-3xl hover:bg-slate-900">
        {text}
      </span>
    </button>
  );
};

export default FancyLargeButton;
