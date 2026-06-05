# Delhivery Logistics Automation - PRD

## Problem Statement
Delhivery franchise owner wants to automate logistics for small businesses. Each business places orders on their website and shipments should auto-manifest with Delhivery.

## Architecture
- Multi-tenant SaaS dashboard
- Auth: Emergent Google Sign-In (cookie + Bearer)
- Backend: FastAPI, MongoDB (per-user data isolation by user_id)
- Frontend: React (CRA + craco) with Shadcn UI, Swiss design (Chivo headings, IBM Plex Sans body)
- Integration: Delhivery API (shared franchise API key across all tenants)

## Implemented Features
- Multi-tenant Google Auth + per-business data isolation
- Forward shipment creation (manual form + webhook /api/orders)
- Reverse pickup (RVP) as separate sub-category under Create Shipment
- Bulk CSV upload with template (weight in grams, HSN, GST, FWD/RVP, invoice)
- Bulk shipment download (CSV with projection, 5000 limit)
- Bulk labels download (ZIP of individual PDFs)
- Pincode serviceability checker on dashboard
- Warehouse registration with Delhivery (handles already-exists case)
- Schedule pickup (date only, time defaults to 10:00:00)
- Track shipment + Download individual label (streamed PDF from Delhivery S3)
- Dashboard with 5 stat cards (Total/Today/In Transit/Delivered/Exceptions)
- Per-business Settings: business name, sender details, GST, pickup location

## Verified
- 33/33 backend pytest cases (auth + multi-tenant isolation)
- 8/8 frontend Playwright flows
- Deployment readiness: PASS

## Next Items (Optional)
- NDR (Non-Delivery Report) auto-handling for reschedule/RTO mitigation
- Tax invoice PDF generator (GST-compliant invoice alongside shipping label)
- SMS/Email notifications to customers (requires Twilio/Resend integration)
- Replace native date picker with shadcn Calendar component
