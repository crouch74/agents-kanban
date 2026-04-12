import { cn } from "@/lib/utils";

function initials(name: string) {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function AvatarStack({
  names,
  className,
}: {
  names: string[];
  className?: string;
}) {
  if (!names.length) {
    return null;
  }

  return (
    <div className={cn("flex items-center pl-1", className)}>
      {names.slice(0, 3).map((name, index) => (
        <span
          key={`${name}-${index}`}
          className="-ml-1 inline-flex h-5 w-5 items-center justify-center rounded-full border border-white bg-zinc-200 text-[10px] font-medium text-zinc-700 first:ml-0"
          title={name}
        >
          {initials(name)}
        </span>
      ))}
    </div>
  );
}

