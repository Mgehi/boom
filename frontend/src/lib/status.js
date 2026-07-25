const STATUS_CLASSES = {
  Delivered: "bg-zinc-900 text-white border-transparent",
  "In Transit": "bg-zinc-100 text-zinc-900 border-zinc-300",
  Exception: "bg-red-50 text-red-700 border-red-200",
  Pending: "bg-white text-zinc-600 border-zinc-200",
  Manifested: "bg-zinc-100 text-zinc-900 border-zinc-300",
};

export const getStatusClass = (status) => STATUS_CLASSES[status] || "bg-white text-zinc-600 border-zinc-200";
