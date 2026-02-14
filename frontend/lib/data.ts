export type OrderStatus = "completed" | "processing" | "review" | "error"

export interface OrderItem {
  sku: string
  product: string
  qty: number
  price: number
  total: number
}

export interface Order {
  id: string
  customer: string
  amount: number
  items: number
  status: OrderStatus
  time: string
  date: string
  message?: string
  warning?: string
  error?: string
  email?: string
  phone?: string
  orderHistory?: string
  parsedItems?: OrderItem[]
  originalText?: string
  customerId?: number
  orderId?: number
}

export interface Client {
  id: string
  customerId: number
  name: string
  email: string
  phone: string
  industry: string
}

export const clients: Client[] = [
  { id: "acme-manufacturing", customerId: 1, name: "Acme Manufacturing", email: "orders@acme-mfg.com", phone: "+1 (415) 555-0142", industry: "Manufacturing" },
  { id: "buildco", customerId: 2, name: "BuildCo", email: "procurement@buildco.io", phone: "+1 (415) 555-0198", industry: "Construction" },
  { id: "techparts-inc", customerId: 3, name: "TechParts Inc", email: "hello@techparts.co", phone: "+1 (650) 555-0177", industry: "Technology" },
  { id: "global-widgets", customerId: 4, name: "Global Widgets", email: "orders@globalwidgets.com", phone: "+1 (212) 555-0134", industry: "Manufacturing" },
  { id: "megacorp", customerId: 5, name: "MegaCorp", email: "supply@megacorp.com", phone: "+1 (310) 555-0156", industry: "Enterprise" },
]

export const orders: Order[] = [
  // --- Acme Manufacturing (5 orders) ---
  {
    id: "ORD-2140214",
    customer: "Acme Manufacturing",
    amount: 12450,
    items: 7,
    status: "completed",
    time: "2m ago",
    date: "2026-02-14",
    message: "Voice: Hey, need 500 blue widgets and 200 gadget pros",
    email: "orders@acme-mfg.com",
    phone: "+1 (415) 555-0142",
    orderHistory: "5th order this month",
    originalText:
      "Hey, need 500 blue widgets and 200 gadget pros. Same specs as last time. Ship to warehouse B.",
    parsedItems: [
      { sku: "WID-001", product: "Blue Widget", qty: 500, price: 15.5, total: 7750 },
      { sku: "GAD-X", product: "Gadget Pro", qty: 200, price: 23.5, total: 4700 },
    ],
  },
  {
    id: "ORD-2140205",
    customer: "Acme Manufacturing",
    amount: 7750,
    items: 3,
    status: "completed",
    time: "3d ago",
    date: "2026-02-11",
    email: "orders@acme-mfg.com",
    phone: "+1 (415) 555-0142",
    originalText: "Need another batch of blue widgets. 500 units please.",
    parsedItems: [
      { sku: "WID-001", product: "Blue Widget", qty: 500, price: 15.5, total: 7750 },
    ],
  },
  {
    id: "ORD-2140190",
    customer: "Acme Manufacturing",
    amount: 9400,
    items: 4,
    status: "completed",
    time: "1w ago",
    date: "2026-02-03",
    email: "orders@acme-mfg.com",
    phone: "+1 (415) 555-0142",
    originalText: "400 gadget pros for warehouse A.",
    parsedItems: [
      { sku: "GAD-X", product: "Gadget Pro", qty: 400, price: 23.5, total: 9400 },
    ],
  },
  {
    id: "ORD-2140160",
    customer: "Acme Manufacturing",
    amount: 4650,
    items: 2,
    status: "completed",
    time: "3w ago",
    date: "2026-01-20",
    email: "orders@acme-mfg.com",
    phone: "+1 (415) 555-0142",
    originalText: "Reorder 300 blue widgets.",
    parsedItems: [
      { sku: "WID-001", product: "Blue Widget", qty: 300, price: 15.5, total: 4650 },
    ],
  },
  {
    id: "ORD-2140120",
    customer: "Acme Manufacturing",
    amount: 6110,
    items: 5,
    status: "completed",
    time: "6w ago",
    date: "2025-12-28",
    email: "orders@acme-mfg.com",
    phone: "+1 (415) 555-0142",
    originalText: "Mixed order: 200 blue widgets and 100 gadget pros.",
    parsedItems: [
      { sku: "WID-001", product: "Blue Widget", qty: 200, price: 15.5, total: 3100 },
      { sku: "GAD-X", product: "Gadget Pro", qty: 100, price: 23.5, total: 2350 },
      { sku: "WID-002", product: "Red Widget", qty: 40, price: 16.5, total: 660 },
    ],
  },

  // --- BuildCo (4 orders) ---
  {
    id: "ORD-2140213",
    customer: "BuildCo",
    amount: 45000,
    items: 12,
    status: "review",
    time: "15m ago",
    date: "2026-02-14",
    warning: "3x usual order size",
    message: "Text: Same as last order but triple everything",
    email: "procurement@buildco.io",
    phone: "+1 (415) 555-0198",
    orderHistory: "3rd order this month",
    originalText: "Same as last order but triple everything. Rush delivery needed by EOW.",
    parsedItems: [
      { sku: "STL-100", product: "Steel Beam A", qty: 300, price: 45.0, total: 13500 },
      { sku: "STL-200", product: "Steel Beam B", qty: 300, price: 52.0, total: 15600 },
      { sku: "BLT-050", product: "Bolt Pack (100)", qty: 150, price: 8.5, total: 1275 },
      { sku: "NUT-050", product: "Nut Pack (100)", qty: 150, price: 6.75, total: 1012.5 },
    ],
  },
  {
    id: "ORD-2140180",
    customer: "BuildCo",
    amount: 15000,
    items: 8,
    status: "completed",
    time: "2w ago",
    date: "2026-01-28",
    email: "procurement@buildco.io",
    phone: "+1 (415) 555-0198",
    originalText: "Standard order: 100 steel beam A, 100 steel beam B, 50 bolt packs.",
    parsedItems: [
      { sku: "STL-100", product: "Steel Beam A", qty: 100, price: 45.0, total: 4500 },
      { sku: "STL-200", product: "Steel Beam B", qty: 100, price: 52.0, total: 5200 },
      { sku: "BLT-050", product: "Bolt Pack (100)", qty: 50, price: 8.5, total: 425 },
    ],
  },
  {
    id: "ORD-2140145",
    customer: "BuildCo",
    amount: 22100,
    items: 6,
    status: "completed",
    time: "5w ago",
    date: "2026-01-10",
    email: "procurement@buildco.io",
    phone: "+1 (415) 555-0198",
    originalText: "Large steel order for the downtown project.",
    parsedItems: [
      { sku: "STL-100", product: "Steel Beam A", qty: 200, price: 45.0, total: 9000 },
      { sku: "STL-200", product: "Steel Beam B", qty: 200, price: 52.0, total: 10400 },
      { sku: "NUT-050", product: "Nut Pack (100)", qty: 400, price: 6.75, total: 2700 },
    ],
  },
  {
    id: "ORD-2140100",
    customer: "BuildCo",
    amount: 8500,
    items: 4,
    status: "completed",
    time: "8w ago",
    date: "2025-12-15",
    email: "procurement@buildco.io",
    phone: "+1 (415) 555-0198",
    originalText: "Initial supplies for Q1 project planning.",
    parsedItems: [
      { sku: "STL-100", product: "Steel Beam A", qty: 80, price: 45.0, total: 3600 },
      { sku: "BLT-050", product: "Bolt Pack (100)", qty: 200, price: 8.5, total: 1700 },
      { sku: "NUT-050", product: "Nut Pack (100)", qty: 200, price: 6.75, total: 1350 },
    ],
  },

  // --- TechParts Inc (3 orders) ---
  {
    id: "ORD-2140212",
    customer: "TechParts Inc",
    amount: 8200,
    items: 3,
    status: "processing",
    time: "1h ago",
    date: "2026-02-14",
    message: "Voice: Following up on quote request...",
    email: "hello@techparts.co",
    phone: "+1 (650) 555-0177",
    orderHistory: "1st order this month",
    originalText:
      "Following up on quote request from last week. Need 100 circuit boards and 50 sensor modules.",
    parsedItems: [
      { sku: "PCB-200", product: "Circuit Board v2", qty: 100, price: 52.0, total: 5200 },
      { sku: "SNS-100", product: "Sensor Module", qty: 50, price: 60.0, total: 3000 },
    ],
  },
  {
    id: "ORD-2140170",
    customer: "TechParts Inc",
    amount: 15600,
    items: 5,
    status: "completed",
    time: "3w ago",
    date: "2026-01-22",
    email: "hello@techparts.co",
    phone: "+1 (650) 555-0177",
    originalText: "Bulk order: 300 circuit boards for production run.",
    parsedItems: [
      { sku: "PCB-200", product: "Circuit Board v2", qty: 300, price: 52.0, total: 15600 },
    ],
  },
  {
    id: "ORD-2140110",
    customer: "TechParts Inc",
    amount: 9000,
    items: 3,
    status: "completed",
    time: "7w ago",
    date: "2025-12-20",
    email: "hello@techparts.co",
    phone: "+1 (650) 555-0177",
    originalText: "150 sensor modules for prototype testing.",
    parsedItems: [
      { sku: "SNS-100", product: "Sensor Module", qty: 150, price: 60.0, total: 9000 },
    ],
  },

  // --- Global Widgets (4 orders) ---
  {
    id: "ORD-2140211",
    customer: "Global Widgets",
    amount: 3890,
    items: 5,
    status: "completed",
    time: "3h ago",
    date: "2026-02-13",
    email: "orders@globalwidgets.com",
    phone: "+1 (212) 555-0134",
    orderHistory: "8th order this month",
    originalText: "Standard reorder of our usual widget package. Deliver next Tuesday.",
    parsedItems: [
      { sku: "WID-001", product: "Blue Widget", qty: 100, price: 15.5, total: 1550 },
      { sku: "WID-002", product: "Red Widget", qty: 80, price: 16.0, total: 1280 },
      { sku: "WID-003", product: "Green Widget", qty: 60, price: 17.67, total: 1060 },
    ],
  },
  {
    id: "ORD-2140200",
    customer: "Global Widgets",
    amount: 5580,
    items: 4,
    status: "completed",
    time: "5d ago",
    date: "2026-02-09",
    email: "orders@globalwidgets.com",
    phone: "+1 (212) 555-0134",
    originalText: "Rush reorder: 200 blue widgets, 100 red widgets.",
    parsedItems: [
      { sku: "WID-001", product: "Blue Widget", qty: 200, price: 15.5, total: 3100 },
      { sku: "WID-002", product: "Red Widget", qty: 100, price: 16.0, total: 1600 },
      { sku: "WID-003", product: "Green Widget", qty: 50, price: 17.67, total: 883.5 },
    ],
  },
  {
    id: "ORD-2140155",
    customer: "Global Widgets",
    amount: 7750,
    items: 3,
    status: "completed",
    time: "4w ago",
    date: "2026-01-15",
    email: "orders@globalwidgets.com",
    phone: "+1 (212) 555-0134",
    originalText: "Large widget order for retail distribution.",
    parsedItems: [
      { sku: "WID-001", product: "Blue Widget", qty: 500, price: 15.5, total: 7750 },
    ],
  },
  {
    id: "ORD-2140105",
    customer: "Global Widgets",
    amount: 3200,
    items: 2,
    status: "review",
    time: "7w ago",
    date: "2025-12-22",
    email: "orders@globalwidgets.com",
    phone: "+1 (212) 555-0134",
    warning: "New product requested",
    originalText: "Need 200 blue widgets. Also inquiring about yellow widgets — do you have them?",
    parsedItems: [
      { sku: "WID-001", product: "Blue Widget", qty: 200, price: 15.5, total: 3100 },
    ],
  },

  // --- MegaCorp (4 orders) ---
  {
    id: "ORD-2140210",
    customer: "MegaCorp",
    amount: 0,
    items: 0,
    status: "error",
    time: "5h ago",
    date: "2026-02-13",
    error: "Unable to parse order format",
    email: "supply@megacorp.com",
    phone: "+1 (310) 555-0156",
    orderHistory: "2nd order this month",
    originalText: "[garbled audio - unable to transcribe]",
    parsedItems: [],
  },
  {
    id: "ORD-2140195",
    customer: "MegaCorp",
    amount: 18200,
    items: 6,
    status: "completed",
    time: "1w ago",
    date: "2026-02-05",
    email: "supply@megacorp.com",
    phone: "+1 (310) 555-0156",
    originalText: "Need 200 circuit boards and 100 sensor modules for R&D.",
    parsedItems: [
      { sku: "PCB-200", product: "Circuit Board v2", qty: 200, price: 52.0, total: 10400 },
      { sku: "SNS-100", product: "Sensor Module", qty: 100, price: 60.0, total: 6000 },
      { sku: "GAD-X", product: "Gadget Pro", qty: 50, price: 23.5, total: 1175 },
    ],
  },
  {
    id: "ORD-2140150",
    customer: "MegaCorp",
    amount: 26000,
    items: 8,
    status: "completed",
    time: "5w ago",
    date: "2026-01-12",
    email: "supply@megacorp.com",
    phone: "+1 (310) 555-0156",
    originalText: "Large procurement: circuit boards and steel for new facility.",
    parsedItems: [
      { sku: "PCB-200", product: "Circuit Board v2", qty: 500, price: 52.0, total: 26000 },
    ],
  },
  {
    id: "ORD-2140095",
    customer: "MegaCorp",
    amount: 12000,
    items: 4,
    status: "processing",
    time: "9w ago",
    date: "2025-12-10",
    email: "supply@megacorp.com",
    phone: "+1 (310) 555-0156",
    originalText: "200 sensor modules for Q1 inventory.",
    parsedItems: [
      { sku: "SNS-100", product: "Sensor Module", qty: 200, price: 60.0, total: 12000 },
    ],
  },
]

export function getOrder(id: string): Order | undefined {
  return orders.find((o) => o.id === id)
}

export function getOrdersForClient(customerName: string): Order[] {
  return orders.filter((o) => o.customer === customerName)
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(amount)
}

export const statusConfig: Record<
  OrderStatus,
  { label: string; className: string; icon: string }
> = {
  completed: {
    label: "Completed",
    className: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800",
    icon: "check",
  },
  processing: {
    label: "Processing",
    className: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800",
    icon: "loader",
  },
  review: {
    label: "Review",
    className: "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800",
    icon: "alert",
  },
  error: {
    label: "Error",
    className: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-400 dark:border-red-800",
    icon: "x",
  },
}
