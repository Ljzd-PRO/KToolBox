import { Button, Surface } from "@heroui/react";
import { Wrench } from "lucide-react";

export function App() {
  return (
    <main className="grid min-h-dvh place-items-center bg-background p-6 text-foreground">
      <Surface className="grid max-w-md gap-4 rounded-lg border border-border p-6">
        <div className="flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-lg bg-accent text-accent-foreground">
            <Wrench aria-hidden="true" size={20} />
          </span>
          <div>
            <h1 className="text-lg font-semibold">KToolBox WebUI</h1>
            <p className="text-sm text-muted-foreground">HeroUI workspace is ready.</p>
          </div>
        </div>
        <Button variant="primary">Continue</Button>
      </Surface>
    </main>
  );
}
