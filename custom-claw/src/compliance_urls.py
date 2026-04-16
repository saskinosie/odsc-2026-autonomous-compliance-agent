"""
Compliance URLs to monitor.
Each entry: (state, subject_area, url)

Add or remove entries here to control what the agent watches.
"""

WATCH_LIST = [
    # State DOE licensure landing pages
    ("Ohio",          "General Licensure", "https://education.ohio.gov/Topics/Teaching/Licensure"),
    ("Texas",         "General Licensure", "https://tea.texas.gov/texas-educators/certification/educator-certification"),
    ("California",    "General Licensure", "https://www.ctc.ca.gov/educator-prep/program-accred/accreditation-overview"),
    ("Florida",       "General Licensure", "https://www.fldoe.org/teaching/certification/"),
    ("New York",      "General Licensure", "https://www.nysed.gov/teaching-certification"),
    ("Pennsylvania",  "General Licensure", "https://www.education.pa.gov/Educators/Certification/Pages/default.aspx"),
    ("Illinois",      "General Licensure", "https://www.isbe.net/Pages/Licensure.aspx"),
    ("Georgia",       "General Licensure", "https://www.gapsc.com/Commission/GetCertified/certification_routes.aspx"),
    ("North Carolina","General Licensure", "https://www.dpi.nc.gov/educators/licensure"),
    ("Virginia",      "General Licensure", "https://www.doe.virginia.gov/teaching-learning-assessment/teaching-in-virginia"),

    # Praxis exam requirements (ETS)
    ("National",      "Praxis Requirements", "https://www.ets.org/praxis/states.html"),
]
