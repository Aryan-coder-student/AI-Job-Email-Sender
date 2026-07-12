import { z } from "zod";

export const newRunSchema = z.object({
  resume: z.any().optional(),
  companies: z.any().optional(),
  companies_url: z.string().url().optional().or(z.literal("")),
  header_row: z.coerce.number().int().min(1).default(1),
  sheet_names: z.string().optional().or(z.literal("")),
  max_rows: z.coerce.number().int().min(1).optional(),
  selected_companies: z.array(z.record(z.unknown())).optional(),
  target_company: z.string().optional().or(z.literal("")),
  recipient_email: z.string().email().optional().or(z.literal("")),
  job_url: z.string().url().optional().or(z.literal("")),
  max_repos: z.coerce.number().int().min(1).max(500),
  max_companies: z.coerce.number().int().min(1).max(500),
  top_matches: z.coerce.number().int().min(1).max(25),
  dry_run: z.boolean(),
  no_enqueue: z.boolean(),
  skip_enrichment: z.boolean(),
  skip_services: z.boolean().default(false),
  clear_graph: z.boolean(),
});

export const draftUpdateSchema = z.object({
  company_name: z.string().optional(),
  to: z.string().email(),
  subject: z.string().min(1),
  body_text: z.string().min(1),
  body_html: z.string().optional().nullable(),
});

export type NewRunSchema = z.infer<typeof newRunSchema>;
export type DraftUpdateSchema = z.infer<typeof draftUpdateSchema>;
