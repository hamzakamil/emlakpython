export interface DatabaseColumn {
  name: string
  type: string
  internal_size: number | null
  null_ok: boolean
  primary_key: boolean
  editable: boolean
  sensitive: boolean
}

export interface DatabaseTable {
  name: string
  label: string
  row_count: number | null
  primary_key: string | null
  columns: DatabaseColumn[]
}

export interface DatabaseOverview {
  database: string
  engine: string
  table_count: number
  tables: DatabaseTable[]
  backup_count: number
}

export interface DatabaseRows {
  table: DatabaseTable
  columns: DatabaseColumn[]
  rows: Record<string, unknown>[]
  count: number
  page: number
  page_size: number
}

export interface DatabaseBackup {
  name: string
  size: number
  created_at: string
}
