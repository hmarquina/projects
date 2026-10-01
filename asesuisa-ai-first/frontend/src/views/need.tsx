import type { Ctx } from "../context";
import { Card } from "../ui";

export function NeedInitiative({ ctx }: { ctx: Ctx }) {
  return (
    <Card title="Selecciona una iniciativa">
      <p className="empty">Esta vista trabaja sobre una iniciativa seleccionada.</p>
      <button onClick={() => ctx.go("initiatives")}>Ir a Initiatives</button>
    </Card>
  );
}
