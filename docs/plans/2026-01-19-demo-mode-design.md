# Demo Mode Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "Launch Demo" button to the landing page that takes users to a fully functional demo of the platform with seeded example data.

**Architecture:** Demo mode intercepts API calls at the client layer and returns mock data instead of calling the real backend. Demo routes reuse existing page components wrapped in a DemoModeProvider context.

**Tech Stack:** React Context, Next.js App Router, TypeScript

---

## Task 1: Create Demo Data File

**Files:**
- Create: `packages/ui/src/lib/demo-data.ts`

Create a single file containing all mock data for the demo:
- 3 example engagements (various statuses)
- 5 data sources (PostgreSQL, Salesforce, Snowflake, S3, Kafka)
- 2 pending approval requests
- Dashboard metrics
- Recent activity items
- Agent clusters and tasks

---

## Task 2: Create Demo Context

**Files:**
- Create: `packages/ui/src/lib/demo-context.tsx`

Create React context for demo mode detection:
- `DemoContext` with boolean value
- `DemoModeProvider` component
- `useIsDemo()` hook for components to check demo status

---

## Task 3: Modify API Layer for Demo Mode

**Files:**
- Modify: `packages/ui/src/lib/api.ts`

Update `apiFetch` function to:
- Check if demo mode is active (via context or route detection)
- Return mock data from demo-data.ts instead of calling real API
- Match endpoints to appropriate mock responses

---

## Task 4: Create Demo Layout and Routes

**Files:**
- Create: `packages/ui/src/app/demo/layout.tsx`
- Create: `packages/ui/src/app/demo/dashboard/page.tsx`
- Create: `packages/ui/src/app/demo/engagements/page.tsx`
- Create: `packages/ui/src/app/demo/engagements/[id]/page.tsx`
- Create: `packages/ui/src/app/demo/approvals/page.tsx`
- Create: `packages/ui/src/app/demo/data-sources/page.tsx`

Layout wraps children in DemoModeProvider.
Page files re-export from main app routes.

---

## Task 5: Add Demo Banner Component

**Files:**
- Create: `packages/ui/src/components/demo-banner.tsx`

Create a banner component that:
- Shows "You're viewing a demo with sample data"
- Links to /docs/quickstart for real setup
- Styled to be noticeable but not intrusive

---

## Task 6: Add Launch Demo Button to Landing Page

**Files:**
- Modify: `packages/ui/src/components/marketing/MarketingNav.tsx`

Add "Launch Demo" button:
- Violet/primary colored button
- Positioned next to "Star on GitHub"
- Links to /demo/dashboard

---

## Task 7: Test and Commit

Run dev server and verify:
- Landing page shows "Launch Demo" button
- Clicking navigates to /demo/dashboard
- Demo dashboard shows mock data
- Navigation within demo stays in /demo/* routes
- Demo banner displays correctly

Commit all changes.
