# UI migration notes

The uploaded React/TanStack prototype was not directly deployable on Streamlit Community Cloud. Its design language was translated into native Streamlit components and CSS:

- navy / coral / teal / warm-beige palette;
- large hero and editorial serif headings;
- multi-step intake cards;
- ranked eligibility cards with percentage meters;
- save/bookmark actions;
- downloadable result table;
- dedicated advisor, feedback and source-intelligence views;
- cumulative visitor count in the global header, sidebar and footer.

The original frontend used US states and US programmes. All production-facing content in this repo is UK-focused and routes by England, Scotland, Wales or Northern Ireland.
