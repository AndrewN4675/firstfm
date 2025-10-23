import Image from "next/image";

export default function Home() {
  return (
    <div className="font-sans flex flex-col flex-1 justify-between min-h-full mt-8 sm:mt-10">
      <div className="text-center sm:text-left sm:pl-4 sm:w-100 md:w-125 xl:w-150 md:pl-8">
        <div className="pb-4">
          <h1 className="font-bold pb-2 sm:text-lg md:text-xl xl:text-2xl">Visualize Your Music, Discover Your Story</h1>
          <p className="">
            Unlock your music map by signing in with your Last.fm account.
          </p>
        </div>
        <button className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md">Start Your Personalized Experience</button>
      </div>
      <div className="text-center pb-4 sm:text-right sm:flex sm:justify-end sm:pr-4 md:pr-8">
        <p className="text-sm text-muted-foreground sm:w-100 md:w-100">This couldn't have been possible without the FirstFM team check them out <a href="#">here!</a> v1.0.0</p>
      </div>
    </div>
  );
}
