import Navbar           from "@/components/landing/Navbar";
import HeroSection      from "@/components/landing/HeroSection";
import FeaturesSection  from "@/components/landing/FeaturesSection";
import HowItWorksSection from "@/components/landing/HowItWorksSection";
import PricingSection   from "@/components/landing/PricingSection";
import Footer           from "@/components/landing/Footer";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-cyber-bg overflow-x-hidden">
      <Navbar />
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <PricingSection />
      <Footer />
    </main>
  );
}
