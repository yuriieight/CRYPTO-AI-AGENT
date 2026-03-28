import React, { useState } from "react";
import axios from "axios";

const API = "http://localhost:8000/api/v1";

export default function Predictions() {
  const [symbol, setSymbol] = useState("BTC/USDT");
  const [result, setResult] = useState<any>(null);

  const predict = async () => {
    const r = await axios.get(`${API}/predictions/predict`, {
      params: { symbol, periods: 7, model: "ensemble" }
    });
    setResult(r.data);
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">ML Predictions</h1>
      <input value={symbol} onChange={e => setSymbol(e.target.value)} className="border p-1 mr-2" />
      <button onClick={predict} className="bg-blue-500 text-white px-4 py-1 rounded">Predict</button>
      {result && <pre className="mt-4">{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
