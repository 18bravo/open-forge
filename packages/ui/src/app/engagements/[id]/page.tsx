import { redirect } from 'next/navigation';

interface EngagementPageProps {
  params: Promise<{ id: string }>;
}

export default async function EngagementPage({ params }: EngagementPageProps) {
  const { id } = await params;
  // Redirect to overview tab
  redirect(`/engagements/${id}/overview`);
}
