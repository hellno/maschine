import Link from "next/link";
import FancyLargeButton from "./FancyLargeButton";

const WelcomeHero = () => {
  return (
    <div className="mx-auto max-w-3xl lg:pt-8">
      <div className="mt-8 flex justify-center">
        <img
          alt="Frameception Logo"
          src="/icon.png"
          className="h-20 w-20 rounded-xl"
        />
      </div>
      <h1 className="mx-auto mt-4 text-pretty text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl md:text-6xl dark:text-gray-100 max-w-xl">
        Create your own Farcaster frame <br className="hidden md:inline" />
        <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          in a Farcaster frame
        </span>
      </h1>
      {/* <div className="mt-4 sm:mt-8 lg:mt-10">
            <div className="flex justify-center space-x-4">
              <span className="rounded-full bg-blue-600/10 px-3 py-1 text-sm/6 font-semibold text-blue-600 ring-1 ring-inset ring-blue-600/10 dark:bg-blue-400/20 dark:text-blue-300 dark:ring-blue-400/30">
                What&apos;s new
              </span>
              <Sheet>
                <SheetTrigger className="inline-flex items-center space-x-2 text-sm/6 font-medium text-gray-600 hover:text-blue-600 dark:text-gray-300 dark:hover:text-blue-400 transition-colors">
                  <PlayCircle className="w-4 h-4" />
                  <span>Watch v0.1 Demo</span>
                </SheetTrigger>
                <SheetContent className="w-full max-w-4xl sm:max-w-6xl">
                  <SheetHeader>
                    <SheetTitle>Frameception Demo</SheetTitle>
                  </SheetHeader>
                  <div
                    className="relative mt-4"
                    style={{ paddingTop: "56.25%" }}
                  >
                    <iframe
                      src="https://player.vimeo.com/video/1047553467?h=af29b86b8e&badge=0&autopause=0&player_id=0&app_id=58479"
                      allow="autoplay; fullscreen; picture-in-picture; clipboard-write; encrypted-media; presentation"
                      className="absolute top-0 left-0 w-full h-full rounded-lg"
                      title="frameception-demo"
                    />
                  </div>
                </SheetContent>
              </Sheet>
            </div>
          </div> */}
      <p className="mt-6 mx-8 text-pretty text-lg font-medium text-gray-600 sm:text-xl/8 dark:text-gray-400 max-w-2xl">
        From idea to live frame to share with the world. Create your own
        Farcaster frame right here.
      </p>
      <Link className="mt-8 flex justify-center" href="/projects/new">
        <FancyLargeButton text="Start Building" />
      </Link>
    </div>
  );
};

export default WelcomeHero;
