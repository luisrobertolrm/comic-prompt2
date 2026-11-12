/// Cópia de `LAYOUTS` em sumi-web/src/app/features/projects/editor/editor.component.ts.
/// Colunas/linhas em frações (fr); slots com início (1-based) e quantas trilhas ocupam.
class LayoutSlot {
  final int col;
  final int colSpan;
  final int row;
  final int rowSpan;
  const LayoutSlot(this.col, this.row, {this.colSpan = 1, this.rowSpan = 1});
}

class PageLayout {
  final String label;
  final List<double> cols;
  final List<double> rows;
  final double aspect;
  final List<LayoutSlot> slots;
  const PageLayout(this.label, this.cols, this.rows, this.aspect, this.slots);
}

const pageGap = 10.0;

const pageLayouts = {
  'manga-vertical': PageLayout('Mangá vertical', [1], [1.1, 0.9, 1, 1.1], 5 / 8, [
    LayoutSlot(1, 1),
    LayoutSlot(1, 2),
    LayoutSlot(1, 3),
    LayoutSlot(1, 4),
  ]),
  'grid': PageLayout('Grade ocidental', [1, 1], [1, 1, 1], 5 / 7, [
    LayoutSlot(1, 1, colSpan: 2),
    LayoutSlot(1, 2),
    LayoutSlot(2, 2),
    LayoutSlot(1, 3),
    LayoutSlot(2, 3),
  ]),
  'dynamic': PageLayout('Dinâmico mangá', [2, 1, 1.4], [1.2, 1, 1], 5 / 7, [
    LayoutSlot(1, 1, colSpan: 2),
    LayoutSlot(3, 1, rowSpan: 2),
    LayoutSlot(1, 2, rowSpan: 2),
    LayoutSlot(2, 2),
    LayoutSlot(2, 3, colSpan: 2),
  ]),
};
