import {
  MarketingNav,
  HeroSection,
  ProblemSection,
  CapabilityCards,
  AudienceSegments,
  ArchitectureSection,
  FooterCTA,
} from '@/components/marketing';

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-50">
      <MarketingNav />
      <HeroSection />
      <ProblemSection />
      <CapabilityCards />
      <AudienceSegments />
      <ArchitectureSection />
      <FooterCTA />
    </main>
  );
}
