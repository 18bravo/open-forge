import {
  HeroSection,
  ProblemSection,
  CapabilityCards,
  AudienceSegments,
  ArchitectureSection,
  FooterCTA,
} from '@/components/marketing';

export default function LandingPage() {
  return (
    <main className="flex flex-col">
      <HeroSection />
      <ProblemSection />
      <CapabilityCards />
      <AudienceSegments />
      <ArchitectureSection />
      <FooterCTA />
    </main>
  );
}
