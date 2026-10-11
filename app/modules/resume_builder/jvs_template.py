from __future__ import annotations

from app.modules.resume_builder.model import ProfessionalProfile


def render_jvs_template(profile: ProfessionalProfile, escape) -> str:
    """Self-contained adaptation of JV's Resume Template (LPPL 1.3c)."""
    contact = " $|$ ".join(filter(None, [profile.phone, profile.email, *profile.links]))
    education = "\n".join(
        rf"\resumeSubheading{{{escape(item.title)}}}{{{escape(item.date)}}}{{{escape(item.subtitle)}}}{{}}"
        for item in profile.education
    )
    experience = "\n".join(
        rf"\resumeSubheading{{{escape(item.title)}}}{{{escape(item.date)}}}{{{escape(item.subtitle)}}}{{}}\resumeItemListStart\resumeItem{{{escape(item.description)}}}\resumeItemListEnd"
        for item in profile.experiences
    )
    return rf"""% JV's Resume Template by Jaskirat Singh (LPPL 1.3c)
% Self-contained adaptation for AI Job Email Sender
\documentclass[letterpaper,11pt]{{article}}
\usepackage[empty]{{fullpage}}
\usepackage{{titlesec}}
\usepackage[usenames,dvipsnames]{{color}}
\usepackage{{enumitem}}
\usepackage[hidelinks]{{hyperref}}
\usepackage{{fancyhdr}}
\usepackage[english]{{babel}}
\usepackage{{tabularx}}
\pagestyle{{fancy}}
\fancyhf{{}}
\renewcommand{{\headrulewidth}}{{0pt}}
\renewcommand{{\footrulewidth}}{{0pt}}
\addtolength{{\oddsidemargin}}{{-0.6in}}
\addtolength{{\evensidemargin}}{{-0.5in}}
\addtolength{{\textwidth}}{{1.19in}}
\addtolength{{\topmargin}}{{-.7in}}
\addtolength{{\textheight}}{{1.4in}}
\raggedbottom
\raggedright
\setlength{{\tabcolsep}}{{0in}}
\titleformat{{\section}}{{\vspace{{-4pt}}\scshape\raggedright\large\bfseries}}{{}}{{0em}}{{}}[\color{{black}}\titlerule \vspace{{-5pt}}]
\newcommand{{\resumeItem}}[1]{{\item\small{{{{#1 \vspace{{-2pt}}}}}}}}
\newcommand{{\resumeSubheading}}[4]{{\vspace{{-2pt}}\item\begin{{tabular*}}{{1.0\textwidth}}[t]{{l@{{\extracolsep{{\fill}}}}r}}\textbf{{#1}} & \textbf{{\small #2}} \\\textit{{\small#3}} & \textit{{\small #4}} \\\end{{tabular*}}\vspace{{-7pt}}}}
\newcommand{{\resumeProjectHeading}}[2]{{\item\begin{{tabular*}}{{1.001\textwidth}}{{l@{{\extracolsep{{\fill}}}}r}}\small#1 & \textbf{{\small #2}}\\\end{{tabular*}}\vspace{{-7pt}}}}
\newcommand{{\resumeSubHeadingListStart}}{{\begin{{itemize}}[leftmargin=0.0in,label={{}}]}}
\newcommand{{\resumeSubHeadingListEnd}}{{\end{{itemize}}}}
\newcommand{{\resumeItemListStart}}{{\begin{{itemize}}}}
\newcommand{{\resumeItemListEnd}}{{\end{{itemize}}\vspace{{-5pt}}}}
\begin{{document}}
\begin{{center}}{{\Huge\scshape {escape(profile.name)}}}\\\vspace{{1pt}}\small {escape(contact)}\end{{center}}
{escape(profile.summary)}
\section{{Education}}
\resumeSubHeadingListStart
{education}
\resumeSubHeadingListEnd
\section{{Experience}}
\resumeSubHeadingListStart
{experience}
\resumeSubHeadingListEnd
% RESUME-BUILDER:TAILORED-START
% Company-tailored GitHub projects are inserted here.
% RESUME-BUILDER:TAILORED-END
\end{{document}}
"""
