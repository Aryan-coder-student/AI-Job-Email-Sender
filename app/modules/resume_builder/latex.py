from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from app.modules.resume_builder.model import ProfileItem, ResumeDocument

LATEX_ESCAPES = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
FORBIDDEN = re.compile(r"\\(?:write18|input|include|openout|read|usepackage\s*\{shellesc\}|immediate)", re.IGNORECASE)


def escape_latex(value: str) -> str:
    return "".join(LATEX_ESCAPES.get(char, char) for char in value)


class LatexRenderer:
    def render(self, document: ResumeDocument) -> str:
        if document.custom_latex is not None:
            validate_latex(document.custom_latex)
            return document.custom_latex
        profile = document.profile
        selected = set(document.selected_item_ids)
        sections = {
            "summary": self._text_section("Summary", profile.summary),
            "skills": self._text_section("Skills", ", ".join(profile.skills)),
            "experience": self._items("Experience", profile.experiences, selected),
            "projects": self._items("Projects", profile.projects, selected),
            "education": self._items("Education", profile.education, selected, always=True),
            "certifications": self._items("Certifications", profile.certifications, selected),
            "publications": self._items("Publications", profile.publications, selected),
        }
        body = "\n".join(sections.get(name, "") for name in document.section_order)
        spacing = "9pt" if document.template == "compact" else "10pt"
        source = rf"""\documentclass[{spacing}]{{article}}
\usepackage[margin=0.65in]{{geometry}}
\usepackage[hidelinks]{{hyperref}}
\usepackage{{enumitem}}
\setlist[itemize]{{nosep,leftmargin=*}}
\pagestyle{{empty}}
\begin{{document}}
\begin{{center}}
{{\LARGE\bfseries {escape_latex(profile.name)}}}\\
{escape_latex(profile.headline)}\\
{escape_latex(' | '.join(filter(None, [profile.email, profile.phone, *profile.links])))}
\end{{center}}
{body}
\end{{document}}
"""
        validate_latex(source)
        return source

    def tailor_existing(
        self,
        source: str,
        *,
        company_name: str,
        role: str,
        projects: list[ProfileItem],
        technical_keywords: list[str],
        nontechnical_keywords: list[str],
    ) -> str:
        """Preserve the supplied template and replace only the managed tailoring block."""
        validate_latex(source)
        start = "% RESUME-BUILDER:TAILORED-START"
        end = "% RESUME-BUILDER:TAILORED-END"
        project_lines = [
            rf"\item \textbf{{{escape_latex(item.title)}}} -- {escape_latex(item.description)}"
            for item in projects
        ]
        parts = [
            start,
            rf"\section*{{Target: {escape_latex(company_name)} -- {escape_latex(role)}}}",
        ]
        if technical_keywords:
            parts.append(rf"\textbf{{Technical keywords:}} {escape_latex(', '.join(technical_keywords))}\\")
        if nontechnical_keywords:
            parts.append(rf"\textbf{{Domain keywords:}} {escape_latex(', '.join(nontechnical_keywords))}")
        if project_lines:
            parts.extend([r"\subsection*{Most relevant projects}", r"\begin{itemize}", *project_lines, r"\end{itemize}"])
        parts.append(end)
        block = "\n".join(parts)
        managed = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
        tailored = managed.sub(lambda _: block, source) if managed.search(source) else source.replace(r"\end{document}", block + "\n" + r"\end{document}")
        validate_latex(tailored)
        return tailored

    @staticmethod
    def _text_section(title: str, value: str) -> str:
        return f"\\section*{{{title}}}\n{escape_latex(value)}" if value.strip() else ""

    @staticmethod
    def _items(title: str, items: list[ProfileItem], selected: set[str], always: bool = False) -> str:
        active = [item for item in items if always or item.id in selected]
        if not active:
            return ""
        lines = [f"\\section*{{{title}}}", "\\begin{itemize}"]
        for item in active:
            heading = " --- ".join(filter(None, [item.title, item.subtitle, item.date]))
            lines.append(f"\\item \\textbf{{{escape_latex(heading)}}} {escape_latex(item.description)}")
        lines.append("\\end{itemize}")
        return "\n".join(lines)


def validate_latex(source: str) -> None:
    if FORBIDDEN.search(source):
        raise ValueError("LaTeX source contains a forbidden file or shell command.")
    if source.count("{") != source.count("}"):
        raise ValueError("LaTeX source has unbalanced braces.")
    if "\\begin{document}" not in source or "\\end{document}" not in source:
        raise ValueError("LaTeX source must contain a document environment.")


class PdfLatexCompiler:
    def compile(self, source: str, output_dir: Path) -> bytes:
        validate_latex(source)
        executable = shutil.which("pdflatex")
        if executable is None:
            raise RuntimeError("pdflatex is not installed on the API server.")
        output_dir.mkdir(parents=True, exist_ok=True)
        tex_path = output_dir / "resume.tex"
        tex_path.write_text(source, encoding="utf-8")
        result = subprocess.run(
            [executable, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
            cwd=output_dir, capture_output=True, text=True, timeout=20, check=False,
        )
        pdf_path = output_dir / "resume.pdf"
        if result.returncode != 0 or not pdf_path.exists():
            raise ValueError((result.stdout or result.stderr)[-1500:] or "LaTeX compilation failed.")
        return pdf_path.read_bytes()
