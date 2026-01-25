'use client';

/**
 * NDS Explorer - 2026 National Defense Strategy Interactive Explorer
 * An educational tool for understanding U.S. defense strategy
 */

import React, { useState } from 'react';

type SectionId = 'overview' | 'lines-of-effort' | 'threats' | 'regions' | 'operations';

interface LOEComponent {
  name: string;
  desc: string;
}

interface LineOfEffort {
  id: number;
  title: string;
  icon: string;
  color: string;
  priority: string;
  summary: string;
  components: LOEComponent[];
  doctrine?: string;
  regions?: string[];
}

interface ThreatActor {
  id: string;
  name: string;
  icon: string;
  level: string;
  color: string;
  threats: string[];
  keyTerrain?: string[];
  response: string;
  implications?: string;
  assessment?: string;
  operations?: string[];
}

interface RegionalApproach {
  id: string;
  name: string;
  usRole: string;
  allyRole: string;
  focus: string;
  icon: string;
}

interface Operation {
  name: string;
  target: string;
  status: string;
}

const linesOfEffort: LineOfEffort[] = [
  {
    id: 1,
    title: "Defend the U.S. Homeland",
    icon: "🛡️",
    color: "#C9A227",
    priority: "HIGHEST",
    summary: "Border security, counter narco-terrorism, secure key terrain in Western Hemisphere",
    components: [
      { name: "Secure Borders", desc: "Border security is national security. Seal borders, repel invasion, coordinate with DHS." },
      { name: "Counter Narco-Terrorists", desc: "Degrade narco-terrorist organizations across the Americas. Prepared for unilateral action if needed." },
      { name: "Secure Key Terrain", desc: "Guarantee U.S. access to Greenland, Gulf of America, Panama Canal. Monroe Doctrine enforcement." },
      { name: "Golden Dome for America", desc: "Missile defense with focus on defeating large barrages. Counter-UAS capabilities." },
      { name: "Nuclear Modernization", desc: "Strong, secure, effective nuclear arsenal. Deterrence and escalation management." },
      { name: "Cyber Defense", desc: "Bolster cyber defenses for military and civilian targets. Deter/degrade cyber threats." },
      { name: "Counter Islamic Terrorists", desc: "Resource-sustainable approach focused on groups capable of striking Homeland." }
    ],
    doctrine: "TRUMP COROLLARY TO THE MONROE DOCTRINE"
  },
  {
    id: 2,
    title: "Deter China in the Indo-Pacific",
    icon: "⚔️",
    color: "#2E5A88",
    priority: "CRITICAL",
    summary: "Through strength, not confrontation. Denial defense along First Island Chain.",
    components: [
      { name: "Military-to-Military Engagement", desc: "Wider range of communications with PLA. Focus on strategic stability and de-escalation." },
      { name: "First Island Chain Defense", desc: "Build, posture, and sustain a strong denial defense along the FIC." },
      { name: "Allied Integration", desc: "Incentivize and enable regional allies to contribute to collective defense." },
      { name: "Deterrence by Denial", desc: "Make clear any aggression will fail and is not worth attempting." },
      { name: "Global Strike Capability", desc: "Maintain ability to conduct devastating strikes anywhere, including from CONUS." }
    ],
    doctrine: "PEACE THROUGH STRENGTH"
  },
  {
    id: 3,
    title: "Increase Burden-Sharing",
    icon: "🤝",
    color: "#4A7C59",
    priority: "HIGH",
    summary: "Allies take primary responsibility for their defense with limited U.S. support.",
    components: [
      { name: "5% GDP Standard", desc: "3.5% on core military + 1.5% security-related spending. Set at NATO Hague Summit." },
      { name: "Model Ally Incentives", desc: "Prioritize cooperation with allies visibly doing more against regional threats." },
      { name: "Arms Sales & Defense Industrial Collaboration", desc: "Enable allies to field forces quickly through equipment and technology sharing." },
      { name: "Force & Operational Planning", desc: "Close collaboration to bolster allied readiness for key missions." }
    ],
    regions: ["Western Hemisphere", "Europe", "Middle East", "Africa", "Korean Peninsula"],
    doctrine: "AMERICA FIRST ENGAGEMENT"
  },
  {
    id: 4,
    title: "Supercharge the U.S. DIB",
    icon: "🏭",
    color: "#8B4513",
    priority: "FOUNDATIONAL",
    summary: "National mobilization to rebuild defense industrial capacity at scale.",
    components: [
      { name: "Production Capacity", desc: "Reinvest in U.S. defense production, building out capacity and empowering innovators." },
      { name: "Technology Adoption", desc: "Adopt AI and other advances. Clear outdated policies and regulations." },
      { name: "Allied Production", desc: "Leverage allied and partner production to meet requirements and incentivize spending." },
      { name: "Sustainment", desc: "Bolster organic sustainment capabilities, grow nontraditional vendors." },
      { name: "Arsenal of Democracy", desc: "Return to being world's premier arsenal—produce for ourselves and allies at scale." }
    ],
    doctrine: "NATIONAL MOBILIZATION"
  }
];

const threatEnvironment: ThreatActor[] = [
  {
    id: "homeland",
    name: "Homeland & Hemisphere",
    icon: "🏠",
    level: "DIRECT",
    color: "#DC143C",
    threats: [
      "Illegal migration flood",
      "Narcotics trafficking (FTOs)",
      "Adversary influence in hemisphere",
      "Loss of access to key terrain"
    ],
    keyTerrain: ["Panama Canal", "Gulf of America", "Greenland"],
    response: "Trump Corollary to Monroe Doctrine"
  },
  {
    id: "china",
    name: "People's Republic of China",
    icon: "🐉",
    level: "PACING",
    color: "#B22222",
    threats: [
      "Historic military buildup (speed, scale, quality)",
      "Western Pacific operational capabilities",
      "Long-range strike capabilities",
      "Potential Indo-Pacific domination"
    ],
    implications: "U.S. access to world's economic center of gravity at risk",
    response: "Denial defense along First Island Chain"
  },
  {
    id: "russia",
    name: "Russia",
    icon: "🐻",
    level: "PERSISTENT",
    color: "#8B0000",
    threats: [
      "World's largest nuclear arsenal",
      "Undersea, space, cyber capabilities",
      "Threat to NATO eastern members",
      "Ukraine war industrial capacity"
    ],
    assessment: "Persistent but manageable. European NATO far outpaces economically ($26T vs $2T GDP).",
    response: "NATO allies take primary responsibility"
  },
  {
    id: "iran",
    name: "Iran",
    icon: "☪️",
    level: "DEGRADED",
    color: "#CD853F",
    threats: [
      "Potential nuclear reconstitution",
      "Proxy network rebuilding",
      "Intent to destroy Israel",
      "Regional instability"
    ],
    operations: ["MIDNIGHT HAMMER", "12-Day War support", "ROUGH RIDER"],
    response: "Empower regional allies; Israel as model ally"
  },
  {
    id: "dprk",
    name: "North Korea (DPRK)",
    icon: "🚀",
    level: "NUCLEAR",
    color: "#FF4500",
    threats: [
      "Nuclear forces capable of striking CONUS",
      "Conventional/nuclear threat to ROK/Japan",
      "WMD delivery capabilities",
      "Growing sophistication"
    ],
    response: "ROK primary responsibility with limited U.S. support"
  }
];

const regionalApproaches: RegionalApproach[] = [
  {
    id: "hemisphere",
    name: "Western Hemisphere",
    usRole: "Dominant",
    allyRole: "Canada, Mexico, regional partners",
    focus: "Border security, counter narco-terror, key terrain access",
    icon: "🌎"
  },
  {
    id: "europe",
    name: "Europe",
    usRole: "Critical but Limited Support",
    allyRole: "NATO takes primary responsibility",
    focus: "Conventional defense, Ukraine support",
    icon: "🏰"
  },
  {
    id: "middleeast",
    name: "Middle East",
    usRole: "Enable & Empower",
    allyRole: "Israel, Gulf partners lead",
    focus: "Counter Iran, Abraham Accords expansion",
    icon: "🕌"
  },
  {
    id: "africa",
    name: "Africa",
    usRole: "Minimal Footprint",
    allyRole: "Partners lead CT efforts",
    focus: "Prevent Homeland-threatening terror",
    icon: "🌍"
  },
  {
    id: "korea",
    name: "Korean Peninsula",
    usRole: "Critical but Limited Support",
    allyRole: "ROK primary responsibility",
    focus: "Deter DPRK, posture update",
    icon: "🇰🇷"
  },
  {
    id: "indopacific",
    name: "Indo-Pacific",
    usRole: "Lead with Allies",
    allyRole: "Regional allies contribute to FIC defense",
    focus: "Denial defense, balance of power",
    icon: "🌏"
  }
];

const operations: Operation[] = [
  { name: "ABSOLUTE RESOLVE", target: "Maduro/Venezuela", status: "Complete" },
  { name: "MIDNIGHT HAMMER", target: "Iran Nuclear Program", status: "Complete" },
  { name: "ROUGH RIDER", target: "Houthis", status: "Complete" },
  { name: "SOUTHERN SPEAR", target: "Narco-terrorists", status: "Ongoing" }
];

const ppbeTimeline = {
  description: 'PPBE operates on overlapping cycles - while one year executes, the next is being budgeted, the following is being programmed, and future years are being planned.',
  cycles: [
    { phase: 'Execution', yearOffset: 0, label: 'Current Year' },
    { phase: 'Budgeting', yearOffset: 1, label: 'Budget Year' },
    { phase: 'Programming', yearOffset: 2, label: 'Program Year' },
    { phase: 'Planning', yearOffset: 3, label: 'Planning Years (FYDP)' }
  ]
};

export function NDSExplorer() {
  const [activeSection, setActiveSection] = useState<SectionId>('overview');
  const [activeLOE, setActiveLOE] = useState<number | null>(null);
  const [activeThreat, setActiveThreat] = useState<string | null>(null);
  const [activeRegion, setActiveRegion] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-200 font-sans">
      {/* Header */}
      <header className="bg-gradient-to-r from-amber-900/20 to-amber-900/5 border-b-2 border-amber-600 px-8 py-5 flex items-center justify-between">
        <div className="flex items-center gap-5">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center text-3xl shadow-lg shadow-amber-500/30">
            🦅
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-wider text-amber-500 drop-shadow">
              2026 NATIONAL DEFENSE STRATEGY
            </h1>
            <p className="text-sm text-slate-500 tracking-widest uppercase mt-1">
              Department of War • Interactive Explorer
            </p>
          </div>
        </div>
        <div className="bg-amber-500/20 px-4 py-2 rounded border border-amber-500 text-xs tracking-widest text-green-400">
          UNCLASSIFIED
        </div>
      </header>

      {/* Navigation */}
      <nav className="flex bg-black/30 border-b border-amber-500/30">
        {(['overview', 'lines-of-effort', 'threats', 'regions', 'operations'] as SectionId[]).map(section => (
          <button
            key={section}
            onClick={() => {
              setActiveSection(section);
              setActiveLOE(null);
              setActiveThreat(null);
              setActiveRegion(null);
            }}
            className={`
              px-7 py-4 border-b-[3px] text-sm font-semibold tracking-wider uppercase transition-all
              ${activeSection === section
                ? 'bg-gradient-to-b from-amber-500/30 to-amber-500/10 border-amber-500 text-amber-500'
                : 'border-transparent text-slate-500 hover:text-slate-300'
              }
            `}
          >
            {section.replace('-', ' ')}
          </button>
        ))}
      </nav>

      {/* Main Content */}
      <main className="p-8 max-w-7xl mx-auto">

        {/* Overview Section */}
        {activeSection === 'overview' && (
          <div className="animate-fadeIn">
            <div className="bg-gradient-to-br from-amber-500/10 to-black/20 border border-amber-500/30 rounded-xl p-8 mb-8">
              <h2 className="text-amber-500 text-xl font-semibold mb-4">
                "RESTORING PEACE THROUGH STRENGTH FOR A NEW GOLDEN AGE OF AMERICA"
              </h2>
              <p className="text-slate-400 leading-relaxed">
                This Strategy reflects a fundamental shift from previous approaches—prioritizing Americans' concrete interests
                with flexible realism. It moves away from grandiose strategies untethered from practical American interests,
                focusing instead on the most consequential threats to U.S. security, freedom, and prosperity.
              </p>
            </div>

            {/* Core Logic Diagram - LOE Cards */}
            <div className="grid grid-cols-4 gap-5 mb-8">
              {linesOfEffort.map((loe) => (
                <div
                  key={loe.id}
                  onClick={() => { setActiveSection('lines-of-effort'); setActiveLOE(loe.id); }}
                  className="relative rounded-xl p-6 cursor-pointer transition-all duration-300 hover:-translate-y-1 group"
                  style={{
                    background: `linear-gradient(135deg, ${loe.color}20 0%, rgba(0,0,0,0.4) 100%)`,
                    border: `1px solid ${loe.color}60`
                  }}
                >
                  <div
                    className="absolute top-3 right-3 px-2 py-1 rounded text-xs font-bold tracking-wide"
                    style={{ backgroundColor: loe.color, color: '#000' }}
                  >
                    LOE {loe.id}
                  </div>
                  <div className="text-4xl mb-3">{loe.icon}</div>
                  <h3 className="font-semibold mb-2" style={{ color: loe.color }}>
                    {loe.title}
                  </h3>
                  <p className="text-slate-500 text-sm leading-relaxed">
                    {loe.summary}
                  </p>
                  <div
                    className="mt-4 px-3 py-2 bg-black/30 rounded text-xs font-semibold tracking-wide"
                    style={{ color: loe.color }}
                  >
                    PRIORITY: {loe.priority}
                  </div>
                </div>
              ))}
            </div>

            {/* Key Principles */}
            <div className="grid grid-cols-2 gap-5">
              <div className="bg-black/30 border border-amber-500/20 rounded-xl p-6">
                <h3 className="text-amber-500 mb-4 text-base tracking-wide">
                  ✦ WHAT THIS STRATEGY IS
                </h3>
                <ul className="text-slate-400 space-y-2 list-disc pl-5">
                  <li>Practical focus on real, credible threats to Americans</li>
                  <li>Flexible, practical realism</li>
                  <li>Clear prioritization of gravest threats</li>
                  <li>Burden-sharing with capable allies</li>
                  <li>Defense industrial revitalization</li>
                </ul>
              </div>
              <div className="bg-black/30 border border-red-900/30 rounded-xl p-6">
                <h3 className="text-red-400 mb-4 text-base tracking-wide">
                  ✗ WHAT THIS STRATEGY REJECTS
                </h3>
                <ul className="text-slate-400 space-y-2 list-disc pl-5">
                  <li>Grandiose nation-building abroad</li>
                  <li>Conflating U.S. interests with rest of world</li>
                  <li>Subsidizing allies' defense</li>
                  <li>Interventionism and endless wars</li>
                  <li>Utopian idealism over realism</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Lines of Effort Section */}
        {activeSection === 'lines-of-effort' && (
          <div className="animate-fadeIn flex gap-8">
            {/* LOE List */}
            <div className="w-80 flex-shrink-0 space-y-3">
              {linesOfEffort.map(loe => (
                <div
                  key={loe.id}
                  onClick={() => setActiveLOE(activeLOE === loe.id ? null : loe.id)}
                  className="rounded-xl p-5 cursor-pointer transition-all"
                  style={{
                    background: activeLOE === loe.id
                      ? `linear-gradient(90deg, ${loe.color}30 0%, transparent 100%)`
                      : 'rgba(0,0,0,0.2)',
                    border: `1px solid ${activeLOE === loe.id ? loe.color : 'rgba(255,255,255,0.1)'}`
                  }}
                >
                  <div className="flex items-center gap-4">
                    <div
                      className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
                      style={{ background: `linear-gradient(135deg, ${loe.color} 0%, ${loe.color}80 100%)` }}
                    >
                      {loe.icon}
                    </div>
                    <div>
                      <div className="text-xs font-bold tracking-wide" style={{ color: loe.color }}>
                        LINE OF EFFORT {loe.id}
                      </div>
                      <div className="font-semibold mt-1">{loe.title}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* LOE Detail */}
            <div className="flex-1">
              {activeLOE ? (
                <div
                  className="bg-black/30 rounded-xl p-8"
                  style={{ border: `1px solid ${linesOfEffort[activeLOE-1].color}40` }}
                >
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h2 className="text-2xl font-semibold mb-2" style={{ color: linesOfEffort[activeLOE-1].color }}>
                        {linesOfEffort[activeLOE-1].icon} {linesOfEffort[activeLOE-1].title}
                      </h2>
                      <p className="text-slate-500">{linesOfEffort[activeLOE-1].summary}</p>
                    </div>
                    <div
                      className="px-4 py-2 rounded font-bold text-sm tracking-wide"
                      style={{ backgroundColor: linesOfEffort[activeLOE-1].color, color: '#000' }}
                    >
                      {linesOfEffort[activeLOE-1].priority}
                    </div>
                  </div>

                  {linesOfEffort[activeLOE-1].doctrine && (
                    <div
                      className="mb-6 px-5 py-4 rounded-r-lg"
                      style={{
                        background: `linear-gradient(90deg, ${linesOfEffort[activeLOE-1].color}20 0%, transparent 100%)`,
                        borderLeft: `4px solid ${linesOfEffort[activeLOE-1].color}`
                      }}
                    >
                      <span className="text-xs text-slate-500 tracking-wide">DOCTRINE: </span>
                      <span className="font-bold" style={{ color: linesOfEffort[activeLOE-1].color }}>
                        {linesOfEffort[activeLOE-1].doctrine}
                      </span>
                    </div>
                  )}

                  <h4 className="text-amber-500 mb-4 text-sm tracking-wide">KEY COMPONENTS</h4>
                  <div className="grid grid-cols-2 gap-3">
                    {linesOfEffort[activeLOE-1].components.map((comp, i) => (
                      <div key={i} className="bg-black/30 border border-white/10 rounded-lg p-4">
                        <div className="font-semibold mb-2" style={{ color: linesOfEffort[activeLOE-1].color }}>
                          {comp.name}
                        </div>
                        <div className="text-slate-500 text-sm leading-relaxed">
                          {comp.desc}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-96 bg-black/20 rounded-xl border border-dashed border-amber-500/30">
                  <p className="text-slate-600">← Select a Line of Effort to view details</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Threats Section */}
        {activeSection === 'threats' && (
          <div className="animate-fadeIn">
            <div className="bg-black/30 border border-amber-500/20 rounded-xl p-6 mb-8">
              <h3 className="text-amber-500 mb-3">Threat Prioritization Framework</h3>
              <p className="text-slate-500 leading-relaxed">
                This Strategy recognizes that not all threats are of equal severity, gravity, and consequence.
                It prioritizes the most direct threats to Americans while positioning allies to counter others.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-5">
              {threatEnvironment.map(threat => (
                <div
                  key={threat.id}
                  onClick={() => setActiveThreat(activeThreat === threat.id ? null : threat.id)}
                  className="rounded-xl p-6 cursor-pointer transition-all"
                  style={{
                    background: activeThreat === threat.id
                      ? `linear-gradient(135deg, ${threat.color}25 0%, rgba(0,0,0,0.4) 100%)`
                      : 'rgba(0,0,0,0.3)',
                    border: `2px solid ${activeThreat === threat.id ? threat.color : 'rgba(255,255,255,0.1)'}`
                  }}
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="text-4xl">{threat.icon}</div>
                    <div
                      className="px-3 py-1 rounded text-xs font-bold tracking-wide text-white"
                      style={{ backgroundColor: threat.color }}
                    >
                      {threat.level}
                    </div>
                  </div>

                  <h3 className="text-white text-lg font-semibold mb-3">{threat.name}</h3>

                  {activeThreat === threat.id && (
                    <div className="mt-4 pt-4" style={{ borderTop: `1px solid ${threat.color}40` }}>
                      <div className="mb-4">
                        <div className="text-xs font-bold mb-2 tracking-wide" style={{ color: threat.color }}>
                          KEY THREATS
                        </div>
                        {threat.threats.map((t, i) => (
                          <div key={i} className="text-slate-400 text-sm py-1.5 border-b border-white/5">
                            • {t}
                          </div>
                        ))}
                      </div>

                      <div className="bg-black/30 p-3 rounded mt-3">
                        <div className="text-xs text-slate-500 tracking-wide mb-1">RESPONSE</div>
                        <div className="text-sm font-semibold" style={{ color: threat.color }}>
                          {threat.response}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Simultaneity Problem */}
            <div className="mt-8 bg-gradient-to-br from-red-900/10 to-black/30 border border-red-900/30 rounded-xl p-6">
              <h3 className="text-red-500 mb-3">⚠️ THE SIMULTANEITY PROBLEM</h3>
              <p className="text-slate-400 leading-relaxed">
                The Strategy addresses the risk of coordinated or opportunistic aggression across multiple theaters.
                Allied burden-sharing is essential: if allies invest properly (5% GDP standard), the combined
                alliance network can generate sufficient forces to deter concurrent threats across all regions.
              </p>
            </div>
          </div>
        )}

        {/* Regions Section */}
        {activeSection === 'regions' && (
          <div className="animate-fadeIn">
            <div className="grid grid-cols-3 gap-5">
              {regionalApproaches.map(region => (
                <div
                  key={region.id}
                  onClick={() => setActiveRegion(activeRegion === region.id ? null : region.id)}
                  className={`
                    rounded-xl p-6 cursor-pointer transition-all
                    ${activeRegion === region.id
                      ? 'bg-gradient-to-br from-amber-500/15 to-black/30 border-amber-500'
                      : 'bg-black/30 border-white/10'
                    }
                    border
                  `}
                >
                  <div className="text-4xl mb-3">{region.icon}</div>
                  <h3 className="text-white text-lg font-semibold mb-2">{region.name}</h3>

                  <div className="mt-4">
                    <div className="flex justify-between py-2.5 border-b border-white/10">
                      <span className="text-slate-500 text-sm">U.S. ROLE</span>
                      <span className="text-amber-500 text-sm font-semibold">{region.usRole}</span>
                    </div>
                    <div className="flex justify-between py-2.5 border-b border-white/10">
                      <span className="text-slate-500 text-sm">ALLY ROLE</span>
                      <span className="text-green-400 text-sm font-semibold text-right max-w-[150px]">
                        {region.allyRole}
                      </span>
                    </div>
                  </div>

                  {activeRegion === region.id && (
                    <div className="mt-4 p-3 bg-black/30 rounded-lg">
                      <div className="text-xs text-slate-500 tracking-wide mb-1">FOCUS AREAS</div>
                      <div className="text-slate-400 text-sm leading-relaxed">{region.focus}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Burden Sharing Visual */}
            <div className="mt-8 bg-gradient-to-br from-green-900/15 to-black/30 border border-green-900/30 rounded-xl p-6">
              <h3 className="text-green-600 mb-5">📊 NATO HAGUE SUMMIT - NEW GLOBAL STANDARD</h3>
              <div className="flex gap-10 items-center">
                <div className="flex-1">
                  <div className="mb-5">
                    <div className="flex justify-between mb-2">
                      <span className="text-slate-500">Core Military Spending</span>
                      <span className="text-green-400 font-bold">3.5% GDP</span>
                    </div>
                    <div className="h-3 bg-black/40 rounded-full overflow-hidden">
                      <div className="w-[70%] h-full bg-gradient-to-r from-green-700 to-green-400 rounded-full" />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-slate-500">Security-Related Spending</span>
                      <span className="text-amber-500 font-bold">1.5% GDP</span>
                    </div>
                    <div className="h-3 bg-black/40 rounded-full overflow-hidden">
                      <div className="w-[30%] h-full bg-gradient-to-r from-amber-600 to-amber-400 rounded-full" />
                    </div>
                  </div>
                </div>
                <div className="w-40 h-40 rounded-full bg-gradient-to-br from-green-700 to-green-900 flex flex-col items-center justify-center shadow-lg shadow-green-700/30">
                  <div className="text-4xl font-bold text-white">5%</div>
                  <div className="text-sm text-green-300 tracking-wide">GDP TOTAL</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Operations Section */}
        {activeSection === 'operations' && (
          <div className="animate-fadeIn">
            <div className="bg-black/30 border border-amber-500/20 rounded-xl p-6 mb-8">
              <h3 className="text-amber-500 mb-3">Referenced Operations</h3>
              <p className="text-slate-500">
                Military operations referenced in the 2026 NDS demonstrating decisive action capability.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-5">
              {operations.map((op, i) => (
                <div
                  key={i}
                  className="bg-gradient-to-br from-amber-500/10 to-black/30 border border-amber-500/30 rounded-xl p-6 relative overflow-hidden"
                >
                  <div
                    className={`
                      absolute top-0 right-0 px-4 py-1.5 text-xs font-bold tracking-wide rounded-bl-lg
                      ${op.status === 'Complete' ? 'bg-green-400' : 'bg-amber-500'}
                      text-black
                    `}
                  >
                    {op.status.toUpperCase()}
                  </div>

                  <div className="text-xs text-slate-500 tracking-widest mb-2">OPERATION</div>
                  <h3 className="text-amber-500 text-2xl font-bold tracking-wider mb-4">
                    {op.name}
                  </h3>
                  <div className="bg-black/30 p-3 rounded-lg">
                    <span className="text-slate-500 text-sm">TARGET: </span>
                    <span className="text-white font-semibold">{op.target}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Capability Statement */}
            <div className="mt-8 bg-gradient-to-r from-amber-500/15 to-black/30 border-l-4 border-amber-500 p-6 rounded-r-xl">
              <p className="text-slate-200 text-lg leading-relaxed italic">
                "By ensuring that the Joint Force is second to none, we will ensure the greatest optionality
                for the President to employ America's armed forces—including the ability to launch decisive
                operations against targets anywhere, including directly from the U.S. Homeland."
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-black/40 border-t border-amber-500/20 px-8 py-5 text-center text-slate-600 text-sm">
        <span className="text-amber-500">2026 National Defense Strategy</span>
        {' • '}Department of War{' • '}
        <span className="text-green-400">UNCLASSIFIED</span>
        {' • '}JAN 23 2026
      </footer>

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.5s ease;
        }
      `}</style>
    </div>
  );
}

export default NDSExplorer;
