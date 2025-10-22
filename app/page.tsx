import Image from "next/image";

export default function Home() {
  return (
    <div className="font-sans grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <a href="http://127.0.0.1:8000/api/lastfm/start/"> Log into your last.fm account</a>
    </div>
  );
}
