export interface MiniCell { cls?: string; text?: string; title?: string }

export function MiniGrid({ rows, cols, cell, onClick }: {
  rows: number; cols: number; cell: (r: number, c: number) => MiniCell; onClick?: (r: number, c: number) => void;
}) {
  const cells: JSX.Element[] = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const info = cell(r, c);
      cells.push(
        <button key={`${r}-${c}`} type="button" className={info.cls ?? ""} title={info.title ?? `r${r}c${c}`} onClick={onClick ? () => onClick(r, c) : undefined}>
          {info.text ?? ""}
        </button>,
      );
    }
  }
  return <div className="mini" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>{cells}</div>;
}
