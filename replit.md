# JayaWarkop POS System

## Overview

This is a Point of Sale (POS) system for a coffee shop/warkop business. The application uses a hybrid architecture with a Python Flask backend serving a Jinja-templated frontend (with Alpine.js for interactivity), alongside a React + TypeScript client that appears to be in early development. The system handles menu display, order management, and transaction processing with Supabase as the external database service.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Primary Backend**: Python Flask (`main.py`) - Handles routing, API endpoints, and Supabase integration
- **Node.js Wrapper**: The server/index.ts spawns the Python Flask process, allowing the system to run within the Replit Node.js environment
- **Database ORM**: Drizzle ORM configured for PostgreSQL (in `shared/schema.ts`) - appears to be set up for future use or migration

### Frontend Architecture
- **Production Frontend**: Jinja2 templates (`templates/index.html`) with Tailwind CSS and Alpine.js for reactive UI
- **React Client** (in development): Located in `client/` directory using:
  - Vite as build tool
  - React with TypeScript
  - Shadcn/UI component library (Radix primitives)
  - TanStack React Query for data fetching
  - Wouter for routing
  - Tailwind CSS with CSS variables for theming

### Data Flow
1. Flask routes serve HTML templates and API endpoints
2. Menu data is fetched from Supabase `menu` table
3. Transactions are saved to Supabase `transactions` table with JSONB items column
4. Order IDs are generated as 8-character alphanumeric strings

### Database Schema
- **Supabase Tables**: `menu` (product catalog), `transactions` (order records)
- **Drizzle Schema**: `users` table defined with id, username, password fields (for future auth)

### Storage Pattern
- In-memory storage class (`MemStorage`) implemented for user management
- Designed with interface abstraction (`IStorage`) for easy database swap

## External Dependencies

### Database & Backend Services
- **Supabase**: Primary database service for menu and transactions
  - Environment variables: `SUPABASE_URL`, `SUPABASE_KEY`
- **PostgreSQL**: Configured via Drizzle for potential migration
  - Environment variable: `DATABASE_URL`

### Key NPM Packages
- `@tanstack/react-query`: Server state management
- `drizzle-orm` / `drizzle-kit`: Database ORM and migrations
- `express`: Node.js server framework (available but Flask is primary)
- Radix UI primitives: Comprehensive component library
- `wouter`: Lightweight React router

### Python Dependencies
- `flask`: Web framework
- `supabase`: Supabase Python client

### Build & Development
- Vite for frontend bundling
- esbuild for server bundling (with specific dependency allowlist for cold start optimization)
- TypeScript for type safety