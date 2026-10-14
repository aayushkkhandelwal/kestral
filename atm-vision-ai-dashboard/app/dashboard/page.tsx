import type { Metadata } from 'next'
import { Dashboard } from '@/components/dashboard/dashboard'

export const metadata: Metadata = {
  title: 'Dashboard — Kestrel',
  description: 'AI-powered CCTV forensics for ATM surveillance.',
}

export default function DashboardPage() {
  return <Dashboard />
}
