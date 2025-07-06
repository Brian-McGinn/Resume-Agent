"use client";

import React from 'react';
import SendMessage from './components/SendMessage';

export default function Home() {
  return (
    <div>
      <main>
        <h1 className="text-xl font-bold mb-4"></h1>
        <SendMessage />
      </main>
      <footer className="row-start-3 flex gap-[24px] flex-wrap items-center justify-center">
      </footer>
    </div>
  );
}
