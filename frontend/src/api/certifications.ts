// Types -------------------------------------------------------------------

export interface Domain {
  id: number
  name: string
  slug: string
  weight_pct: number
  description: string
}

export interface CertificationSummary {
  id: number
  slug: string
  display_name: string
  provider: string
  level: string
  pass_score_pct: number
}

export interface CertificationDetail extends CertificationSummary {
  prompt_context: string
  domains: Domain[]
}

// API calls ---------------------------------------------------------------

export async function listCertifications(): Promise<CertificationSummary[]> {
  const response = await fetch('/api/certifications')
  if (!response.ok) throw new Error(`Failed to fetch certifications: ${response.status}`)
  return response.json() as Promise<CertificationSummary[]>
}

export async function getCertification(slug: string): Promise<CertificationDetail> {
  const response = await fetch(`/api/certifications/${slug}`)
  if (response.status === 404) throw new Error(`Certification not found: ${slug}`)
  if (!response.ok) throw new Error(`Failed to fetch certification: ${response.status}`)
  return response.json() as Promise<CertificationDetail>
}
