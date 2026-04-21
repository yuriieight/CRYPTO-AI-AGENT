import React, { useEffect, useState } from "react";
import axios from "axios";

const API = "http://localhost:8000/api/v1";

export default function Portfolio() {
  const [assets, setAssets]   = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/portfolio`).then(r => {
      setAssets(r.data);
      setLoading(false);
    });
  }, []);

  const totalPnl = assets.reduce((s: number, a: any) => s + (a.pnl || 0), 0);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-2">Portfolio</h1>
      <div className={`text-lg font-semibold mb-4 ${totalPnl >= 0 ? "text-green-500" : "text-red-500"}`}>
        Total P&L: {totalPnl >= 0 ? "+" : ""}{totalPnl.toFixed(2)} USDT
      </div>
      {loading ? <p>Loading…</p> : assets.map((a: any) => (
        <div key={a.symbol} className="flex justify-between border-b py-1">
          <span>{a.symbol}</span>
          <span>{a.amount}</span>
          <span className={a.pnl >= 0 ? "text-green-400" : "text-red-400"}>
            {a.pnl?.toFixed(2)}
          </span>
        </div>
      ))}
    </div>
  );
}
