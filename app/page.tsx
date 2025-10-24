import GenreGraph from "./genre-graph";
import { Analytics } from '@vercel/analytics/next';

export default function Home() {
  return (
    <div className='h-full w-full'>
      <Analytics />
        <div className='h-[90vh] w-full border-b border-[#282828]'>
            <GenreGraph/>
        </div>
        <main className='flex-grow mt-10'>
          <section className='flex justify-center px-4 mb-3'>
            <a href="http://127.0.0.1:8000/api/lastfm/start/"> Log into your last.fm account</a>
          </section>
          
        </main>
    </div>
  );
}
