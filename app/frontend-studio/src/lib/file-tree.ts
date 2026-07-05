export interface FileInfo {
  path: string;
  type: string;
  size: number;
}

export interface TreeNode {
  name: string;
  file?: FileInfo;
  children: Map<string, TreeNode>;
}

export function buildTree(files: FileInfo[]): TreeNode {
  const root: TreeNode = { name: "", children: new Map() };
  for (const file of files) {
    const parts = file.path.replace(/\\/g, "/").split("/");
    let node = root;
    for (let i = 0; i < parts.length - 1; i++) {
      if (!node.children.has(parts[i])) {
        node.children.set(parts[i], { name: parts[i], children: new Map() });
      }
      node = node.children.get(parts[i])!;
    }
    const leaf: TreeNode = {
      name: parts[parts.length - 1],
      file,
      children: new Map(),
    };
    node.children.set(leaf.name, leaf);
  }
  return root;
}

export function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function extType(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase() ?? "";
  const imageExts = ["png", "jpg", "jpeg", "gif", "svg", "webp", "bmp"];
  if (imageExts.includes(ext)) return "image";
  if (["pdf"].includes(ext)) return "pdf";
  if (["csv", "tsv", "psv", "xlsx", "xls", "parquet"].includes(ext)) return "spreadsheet";
  if (["json"].includes(ext)) return "json";
  if (["tex", "cls", "sty", "bib", "typ"].includes(ext)) return "latex";
  if (["html", "htm"].includes(ext)) return "html";
  if (["py", "ts", "tsx", "js", "jsx", "m", "r"].includes(ext)) return "code";
  if (["md", "txt", "log"].includes(ext)) return "text";
  return "file";
}
