"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [message, setMessage] = useState("Loading...");

  useEffect(() => {
    async function loadData() {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/changedRoute`
        );

        const data = await response.json();
        setMessage(data.message);
      } catch (error) {
        console.error(error);
        setMessage("Failed to connect");
      }
    }

    loadData();
  }, []);

  return (
    <main>
      <h1>Chat With Documents</h1>
      <p>{message}</p>
    </main>
  );
}
