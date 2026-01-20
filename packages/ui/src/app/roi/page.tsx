'use client';

import { useState } from 'react';
import { Calculator, DollarSign, Users } from 'lucide-react';

export default function ROIPage() {
  const [engineers, setEngineers] = useState(5);
  const [annualCost, setAnnualCost] = useState(500000);

  const traditionalCost = engineers * annualCost;
  const savings = traditionalCost;

  return (
    <div className="min-h-screen bg-zinc-950 pt-24 pb-16">
      <div className="mx-auto max-w-4xl px-6">
        <div className="text-center mb-12">
          <Calculator className="h-12 w-12 text-violet-500 mx-auto mb-4" />
          <h1 className="text-4xl font-bold text-zinc-50 mb-4">ROI Calculator</h1>
          <p className="text-lg text-zinc-400">See how much you could save by switching to Open Forge.</p>
        </div>

        <div className="grid gap-8 md:grid-cols-2 mb-12">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
            <h2 className="text-xl font-semibold text-zinc-50 mb-6">Your Current Costs</h2>
            <div className="space-y-6">
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-zinc-300 mb-2">
                  <Users className="h-4 w-4" /> Forward-Deployed Engineers
                </label>
                <input type="range" min="1" max="20" value={engineers} onChange={(e) => setEngineers(Number(e.target.value))} className="w-full accent-violet-500" />
                <div className="text-right text-zinc-400">{engineers} engineers</div>
              </div>
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-zinc-300 mb-2">
                  <DollarSign className="h-4 w-4" /> Annual Cost per Engineer
                </label>
                <input type="range" min="200000" max="1000000" step="50000" value={annualCost} onChange={(e) => setAnnualCost(Number(e.target.value))} className="w-full accent-violet-500" />
                <div className="text-right text-zinc-400">${annualCost.toLocaleString()}</div>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-violet-500/50 bg-violet-500/10 p-6">
            <h2 className="text-xl font-semibold text-zinc-50 mb-6">Your Savings</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center py-3 border-b border-zinc-800">
                <span className="text-zinc-400">Traditional Cost</span>
                <span className="text-xl font-semibold text-red-400">${traditionalCost.toLocaleString()}/year</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-zinc-800">
                <span className="text-zinc-400">Open Forge Cost</span>
                <span className="text-xl font-semibold text-green-400">$0/year</span>
              </div>
              <div className="flex justify-between items-center py-3">
                <span className="text-zinc-50 font-semibold">Annual Savings</span>
                <span className="text-3xl font-bold text-violet-400">${savings.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="text-center text-zinc-500 text-sm">* Estimates based on industry averages.</div>
      </div>
    </div>
  );
}
