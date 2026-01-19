import { redirect } from 'next/navigation';

interface EngagementPageProps {
  params: { id: string };
}

export default function EngagementPage({ params }: EngagementPageProps) {
  // Redirect to overview tab
  redirect(`/engagements/${params.id}/overview`);
}
