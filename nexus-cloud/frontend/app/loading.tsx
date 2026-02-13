import { SkeletonCard } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-fade-in">
      {Array.from({ length: 8 }).map((_, i) => (
        <SkeletonCard key={i} lines={i < 4 ? 2 : 4} />
      ))}
    </div>
  );
}
