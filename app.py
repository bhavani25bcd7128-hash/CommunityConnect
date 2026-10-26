from datetime import datetime
import math
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CommunityAI", page_icon="🌱", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.2rem;max-width:1450px}
.hero{padding:1.5rem 1.7rem;border:1px solid #dceae7;border-radius:18px;background:linear-gradient(115deg,#eff8f5,#fff)}
.hero h1{margin:.25rem 0;color:#153c3a;font-size:2.1rem;letter-spacing:-.03em}
.hero p{color:#526765;font-size:1rem;margin-bottom:0}
.kicker{color:#147d72;font-size:.75rem;font-weight:750;letter-spacing:.12em;text-transform:uppercase}
div[data-testid="stMetric"]{background:#fff;border:1px solid #e2e9ed;padding:13px 15px;border-radius:13px}
</style>
""", unsafe_allow_html=True)

CATS = {
"Water & sanitation":["water","drinking","tap","leak","sewage","toilet","sanitation","shortage"],
"Waste management":["garbage","waste","rubbish","trash","dump","cleaning","litter","collection"],
"Transport & roads":["bus","transport","road","traffic","pothole","sidewalk","commute","crossing"],
"Safety & lighting":["unsafe","safety","streetlight","street light","dark","accident","crime","lighting"],
"Health & accessibility":["hospital","clinic","health","ambulance","wheelchair","accessible","doctor"],
"Education & internet":["school","student","education","internet","wifi","wi-fi","computer","library","learning"],
"Food & housing":["food","meal","hostel","housing","shelter","rent","nutrition","hungry"],
"Environment":["tree","pollution","air","smoke","flood","drainage","heat","climate","rain"]}
ACTIONS = {
"Water & sanitation":["Verify the supply issue with affected residents and the relevant water service.","Group reports by neighbourhood and identify who may need urgent support.","Track inspection and repair dates."],
"Waste management":["Compare reports with the published collection schedule.","Identify repeat hotspots before planning extra collection or a cleanup.","Track repeat reports and whether the area stays clear."],
"Transport & roads":["Verify the location and gather safe, relevant evidence.","Review pedestrian access and peak travel times.","Refer a concise issue summary to the relevant transport or public-works team."],
"Safety & lighting":["Validate the location without publishing sensitive personal details.","Request a lighting inspection.","Track repair status; a report alone does not prove a crime."],
"Health & accessibility":["Confirm service details with a qualified provider.","Avoid collecting medical or other sensitive details.","Document access barriers and check improvements."],
"Education & internet":["Identify who is affected and what access is missing.","Explore shared access points, device lending, or connectivity support.","Track reliability and access improvements."],
"Food & housing":["Verify support needs respectfully without collecting names.","Use verified local service directories before referring people.","Track support gaps and service response."],
"Environment":["Verify the location, date, and conditions.","Coordinate with the relevant maintenance or environmental service.","Track follow-up observations."],
"Other":["Clarify what happened, where, and who may be affected.","Identify a relevant service or community group for review.","Agree on a measurable next step."]}

def classify(text):
    text=str(text).lower()
    scores={cat:sum(term in text for term in terms) for cat,terms in CATS.items()}
    best=max(scores,key=scores.get)
    return best if scores[best] else "Other"

def score(severity, urgency, people):
    sev=(severity-1)/4*100
    urg=(urgency-1)/4*100
    reach=min(100, math.log10(max(int(people),1)+1)/math.log10(10001)*100)
    return round(.40*sev+.35*urg+.25*reach,1)

def label(n):
    return "Critical" if n>=85 else "High" if n>=70 else "Medium" if n>=45 else "Low"

def new_report(title, desc, area, people, severity, urgency, lat, lon, evidence):
    n=score(severity,urgency,people)
    return {"Report ID":f"CAI-{datetime.now().strftime('%y%m%d%H%M%S%f')[-9:]}",
    "Issue":title.strip(),"Description":desc.strip(),"Area":area.strip(),
    "Category":classify(title+" "+desc),"People affected (estimate)":int(people),
    "Severity (1–5)":int(severity),"Urgency (1–5)":int(urgency),
    "Priority score":n,"Priority":label(n),"Status":"Needs review",
    "Evidence URL":evidence,"Latitude":lat,"Longitude":lon,
    "Reported at":datetime.now().strftime("%Y-%m-%d %H:%M"),
    "Data source":"Community submission"}

DEMO = [
["DEMO-001","Drinking water supply is irregular","Residents say water has been unavailable for several days in parts of the neighbourhood.","North Ward (illustrative)","Water & sanitation",320,5,5,96.0,"Critical","Needs review",16.5062,80.6480],
["DEMO-002","Garbage collection was missed","Waste is accumulating near a local market and residents report a persistent smell.","Market Road (illustrative)","Waste management",180,3,3,55.0,"Medium","Under review",16.5150,80.6300],
["DEMO-003","Street light near bus stop is broken","The road is dark after sunset and students say the walk feels unsafe.","College Junction (illustrative)","Safety & lighting",95,4,4,73.0,"High","Needs review",16.5200,80.6150],
["DEMO-004","Not enough buses in the evening","People report long waits for buses after 7 PM, affecting college and work travel.","East Bus Route (illustrative)","Transport & roads",240,3,3,58.0,"Medium","In progress",16.5000,80.6600],
["DEMO-005","Wi-Fi is unreliable in the study area","Students report difficulty accessing online learning resources in the library.","Campus Library (illustrative)","Education & internet",75,2,2,33.0,"Low","Needs review",16.4940,80.5000],
["DEMO-006","Drain is blocked after heavy rain","Residents report standing water after rainfall and want the drain checked.","South Lane (illustrative)","Environment",130,4,4,74.0,"High","Needs review",16.5100,80.6400],
["DEMO-007","Ramp access is missing at a public entrance","Wheelchair users may need help accessing the entrance; details require a site check.","Community Centre (illustrative)","Health & accessibility",25,4,3,61.0,"Medium","Needs review",16.5020,80.6350],
["DEMO-008","Pedestrian crossing needs inspection","Residents report difficulty crossing a busy road near a school.","School Road (illustrative)","Transport & roads",210,5,4,83.0,"High","Needs review",16.5170,80.6250],
["DEMO-009","Limited access to learning resources","Learners say they need more access to computers and study materials.","Learning Centre (illustrative)","Education & internet",60,2,3,39.0,"Low","Needs review",None,None],
["DEMO-010","Community clinic waiting times are long","Visitors report long waits and request a review of appointment flow.","Local Clinic (illustrative)","Health & accessibility",140,3,4,65.0,"Medium","Under review",None,None],
["DEMO-011","Public seating is limited near the bus stop","Older residents and people with mobility needs request seating while waiting.","Central Stop (illustrative)","Health & accessibility",80,2,2,30.0,"Low","Needs review",None,None],
["DEMO-012","Food support information is hard to find","Community members want a clear list of verified food support services.","Community-wide (illustrative)","Food & housing",55,3,3,52.0,"Medium","Needs review",None,None]]
COLS=["Report ID","Issue","Description","Area","Category","People affected (estimate)","Severity (1–5)","Urgency (1–5)","Priority score","Priority","Status","Latitude","Longitude"]
if "reports" not in st.session_state:
    df=pd.DataFrame(DEMO,columns=COLS)
    df["Evidence URL"]=""
    df["Reported at"]="2026-10-26"
    df["Data source"]="DEMO DATA — illustrative"
    st.session_state.reports=df
if "nav" not in st.session_state: st.session_state.nav="Overview"

with st.sidebar:
    st.markdown("## 🌱 CommunityAI")
    st.caption("Community needs → clear next steps")
    page=st.radio("Navigate",["Overview","Explore reports","Report a need","Opportunity finder","Map & locations","About this project"],key="nav",label_visibility="collapsed")
    st.divider()
    show_demo=st.toggle("Include sample reports",value=True)
    st.caption("Sample reports are fictional. Reports are held in the current app session; export them before closing.")

all_reports=st.session_state.reports.copy()
reports=all_reports if show_demo else all_reports[all_reports["Data source"]!="DEMO DATA — illustrative"].copy()
st.markdown('<div class="hero"><div class="kicker">Community insight workspace</div><h1>Make community needs easier to understand.</h1><p>Collect local concerns, see which issues may need attention first, and explore practical next steps — with transparent scoring and human review.</p></div>',unsafe_allow_html=True)
st.write("")

if page=="Overview":
    st.subheader("Overview")
    st.caption("A quick picture of the reports in your workspace.")
    if len(reports):
        a,b,c,d=st.columns(4)
        a.metric("Reports received",len(reports))
        b.metric("Critical / high",int(reports["Priority"].isin(["Critical","High"]).sum()))
        c.metric("Estimated people affected",f"{int(reports['People affected (estimate)'].sum()):,}")
        d.metric("Still open",int((reports["Status"]!="Resolved").sum()))
        left,right=st.columns([1.1,1])
        with left:
            st.markdown("#### Issues needing attention")
            queue=reports[reports["Status"]!="Resolved"].sort_values("Priority score",ascending=False).head(7)
            st.dataframe(queue[["Issue","Area","Priority","Priority score","Status"]],width="stretch",hide_index=True)
        with right:
            st.markdown("#### What people are reporting")
            counts=reports["Category"].value_counts().rename_axis("Category").reset_index(name="Reports")
            fig=px.bar(counts,x="Reports",y="Category",orientation="h",color="Reports",color_continuous_scale=["#C8E6E0","#147D72"])
            fig.update_layout(height=340,margin=dict(l=0,r=5,t=5,b=0),coloraxis_showscale=False,yaxis={"categoryorder":"total ascending"},plot_bgcolor="white",paper_bgcolor="white")
            st.plotly_chart(fig,width="stretch")
        x,y,z=st.columns(3)
        x.info("**1 · Collect**\n\nBring community reports into one place.")
        y.info("**2 · Prioritize**\n\nCompare urgency, severity, and estimated reach.")
        z.info("**3 · Act**\n\nUse suggestions as a starting point for local review.")
    else: st.info("No reports are visible. Turn on sample reports or submit a new community need.")

elif page=="Explore reports":
    st.subheader("Explore community reports")
    st.caption("A report is not automatically verified just because it appears here.")
    if len(reports):
        c1,c2,c3=st.columns([1,1,1.3])
        cats=["All categories"]+sorted(reports["Category"].dropna().unique().tolist())
        cat=c1.selectbox("Category",cats)
        pri=c2.selectbox("Priority",["All priorities","Critical","High","Medium","Low"])
        query=c3.text_input("Search",placeholder="Issue, area, or description")
        view=reports.copy()
        if cat!="All categories": view=view[view["Category"]==cat]
        if pri!="All priorities": view=view[view["Priority"]==pri]
        if query.strip():
            mask=view[["Issue","Area","Description"]].fillna("").astype(str).apply(lambda col:col.str.contains(query,case=False,regex=False)).any(axis=1)
            view=view[mask]
        st.caption(f"{len(view)} report(s) match.")
        st.dataframe(view[["Report ID","Issue","Area","Category","People affected (estimate)","Priority score","Priority","Status","Data source"]].sort_values("Priority score",ascending=False),width="stretch",hide_index=True)
        with st.expander("Update a report status"):
            rid=st.selectbox("Choose report ID",view["Report ID"].tolist())
            current=view.loc[view["Report ID"]==rid,"Status"].iloc[0]
            status=st.selectbox("Status",["Needs review","Under review","In progress","Resolved","Rejected"],index=["Needs review","Under review","In progress","Resolved","Rejected"].index(current))
            if st.button("Save status",type="primary"):
                st.session_state.reports.loc[st.session_state.reports["Report ID"]==rid,"Status"]=status
                st.success("Status updated."); st.rerun()
        st.download_button("Download filtered reports (CSV)",view.to_csv(index=False).encode("utf-8"),"communityai_reports.csv","text/csv")
    else: st.info("No reports yet. Add the first one under Report a need.")

elif page=="Report a need":
    st.subheader("Report a community need")
    st.write("Describe the problem in plain language. You do not need to know its category.")
    st.warning("Do not enter names, phone numbers, medical details, or other private information.")
    with st.form("report_form",clear_on_submit=True):
        title=st.text_input("What is the problem? *",placeholder="Example: Drinking water is unavailable on our street")
        desc=st.text_area("Describe what is happening *",placeholder="When does it happen? Who may be affected? What have you observed?",height=120)
        area=st.text_input("Where is it happening? *",placeholder="Neighbourhood, campus block, village, or public landmark")
        c1,c2,c3=st.columns(3)
        people=c1.number_input("Estimated people affected",min_value=1,max_value=1000000,value=50,step=10)
        severity=c2.slider("Severity",1,5,3,help="1 = minor impact, 5 = very serious impact")
        urgency=c3.slider("Urgency",1,5,3,help="1 = can wait, 5 = needs quick attention")
        with st.expander("Optional location and evidence"):
            x,y=st.columns(2)
            lat_s=x.text_input("Latitude",placeholder="Leave blank if unknown")
            lon_s=y.text_input("Longitude",placeholder="Leave blank if unknown")
            evidence=st.text_input("Evidence link",placeholder="Public source or photo URL (optional)")
        submitted=st.form_submit_button("Analyze and add report",type="primary",width="stretch")
        if submitted:
            if not title.strip() or not desc.strip() or not area.strip():
                st.error("Please fill in the problem, description, and location.")
            else:
                lat=lon=None
                try:
                    if lat_s.strip() or lon_s.strip():
                        lat=float(lat_s); lon=float(lon_s)
                        if not (-90<=lat<=90 and -180<=lon<=180): raise ValueError
                except ValueError:
                    st.error("Coordinates must be valid numbers. Latitude is -90 to 90; longitude is -180 to 180."); st.stop()
                row=new_report(title,desc,area,people,severity,urgency,lat,lon,evidence.strip())
                st.session_state.reports=pd.concat([st.session_state.reports,pd.DataFrame([row])],ignore_index=True)
                st.success(f"Report added · {row['Category']} · {row['Priority']} priority · score {row['Priority score']}/100")
                st.info("Category suggestion uses keyword rules. A person should verify the report and score before acting.")
                st.rerun()

elif page=="Opportunity finder":
    st.subheader("Opportunity finder")
    st.caption("Possible next steps to verify locally — not confirmed commitments from organizations.")
    if len(reports):
        options=reports.sort_values("Priority score",ascending=False)
        rid=st.selectbox("Choose an issue",options["Report ID"].tolist(),format_func=lambda x:f"{options.loc[options['Report ID']==x,'Priority'].iloc[0]} · {options.loc[options['Report ID']==x,'Issue'].iloc[0]}")
        row=options[options["Report ID"]==rid].iloc[0]
        a,b=st.columns([2,1])
        a.markdown(f"### {row['Issue']}"); a.write(row["Description"]); a.caption(f"{row['Area']} · {row['Category']} · {row['Report ID']}")
        b.metric("Priority score",f"{row['Priority score']}/100",row["Priority"]); b.caption("Status: "+row["Status"])
        st.markdown("#### Suggested next steps")
        for i,action in enumerate(ACTIONS.get(row["Category"],ACTIONS["Other"]),1):
            st.markdown(f"**{i}.** {action}")
        st.markdown("#### Before taking action")
        st.markdown("- Confirm the concern with affected people or a responsible service.\n- Look for reliable evidence or direct observation.\n- Consider people who may be missing from the reports.\n- Record an owner, next step, and measure of improvement.")
        st.info("Suggestions are category-based checklists, not generated by a live LLM.")
    else: st.info("Add a report to receive suggestions.")

elif page=="Map & locations":
    st.subheader("Map & locations")
    st.caption("Only reports with coordinates appear. Demo coordinates are illustrative, not verified locations.")
    points=reports.dropna(subset=["Latitude","Longitude"]).copy() if len(reports) else pd.DataFrame()
    if len(points):
        st.map(points.rename(columns={"Latitude":"latitude","Longitude":"longitude"}),latitude="latitude",longitude="longitude")
        st.dataframe(points[["Issue","Area","Priority","Latitude","Longitude","Data source"]],width="stretch",hide_index=True)
    else: st.info("No reports have coordinates yet. Reports without coordinates remain visible in the report list.")

else:
    st.subheader("About CommunityAI")
    st.markdown("""
### Why it exists
Communities often share concerns through many channels. CommunityAI organizes reports so recurring needs and possible next steps are easier to see.

### How it works
1. **Collect:** Someone submits a short report.
2. **Categorize:** Keyword rules suggest a topic.
3. **Prioritize:** A score combines severity (40%), urgency (35%), and estimated reach (25%).
4. **Recommend:** A category checklist suggests next steps.
5. **Review:** People validate reports and evidence before decisions are made.

### Reading the score
- Severity and urgency are rated from 1 to 5.
- Estimated reach is normalized so very large numbers do not dominate.
- The score helps organize reports; it is not a validated policy standard or an automatic decision.

### Current limitations
- No live generative AI model is connected yet; categorization is keyword-based.
- Recommendations are checklists, not verified referrals.
- Reports live in the current Streamlit session, not a permanent database.
- Demo reports are fictional; demo coordinates are illustrative.
- People affected may overlap between reports.

### Responsible use
Do not enter sensitive personal information. Validate concerns with affected people and reliable sources. Consider underreported groups and never allocate resources using the score alone.
""")
    st.download_button("Export visible reports (CSV)",reports.to_csv(index=False).encode("utf-8"),"communityai_reports.csv","text/csv")
    if st.button("Reset to demo data"):
        df=pd.DataFrame(DEMO,columns=COLS); df["Evidence URL"]=""; df["Reported at"]="2026-10-26"; df["Data source"]="DEMO DATA — illustrative"
        st.session_state.reports=df; st.success("Demo data restored."); st.rerun()

st.divider()
st.caption("CommunityAI · Hackathon prototype · Human review required · Demo records are illustrative")
