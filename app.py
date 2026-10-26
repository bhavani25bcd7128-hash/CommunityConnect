import math
import uuid
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="CommunityConnect", page_icon="🌱", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.2rem;max-width:1450px}
.hero{padding:1.5rem 1.7rem;border:1px solid #dceae7;border-radius:18px;background:linear-gradient(115deg,#eff8f5,#fff)}
.hero h1{margin:.25rem 0;color:#153c3a;font-size:2.1rem}
.hero p{color:#526765;margin-bottom:0}
div[data-testid="stMetric"]{background:#fff;border:1px solid #e2e9ed;padding:13px 15px;border-radius:13px}
</style>
""", unsafe_allow_html=True)

DB_DEFAULT = "https://communityconnect-1935f-default-rtdb.asia-southeast1.firebasedatabase.app"
AUTH_BASE = "https://identitytoolkit.googleapis.com/v1"
CATS = {
    "Water & sanitation":["water","drinking","tap","leak","sewage","toilet","sanitation","shortage"],
    "Waste management":["garbage","waste","rubbish","trash","dump","cleaning","litter","collection"],
    "Transport & roads":["bus","transport","road","traffic","pothole","sidewalk","commute","crossing"],
    "Safety & lighting":["unsafe","safety","streetlight","street light","dark","accident","crime","lighting"],
    "Health & accessibility":["hospital","clinic","health","ambulance","wheelchair","accessible","doctor"],
    "Education & internet":["school","student","education","internet","wifi","wi-fi","computer","library","learning"],
    "Food & housing":["food","meal","hostel","housing","shelter","rent","nutrition","hungry"],
    "Environment":["tree","pollution","air","smoke","flood","drainage","heat","climate","rain"],
}
ACTIONS = {
    "Water & sanitation":["Verify the supply issue with affected residents and the relevant water service.","Group reports by neighbourhood and identify who may need urgent support.","Track inspection and repair dates."],
    "Waste management":["Compare reports with the published collection schedule.","Identify repeat hotspots before planning extra collection or a cleanup.","Track whether the area stays clear."],
    "Transport & roads":["Verify the location and gather safe evidence.","Review pedestrian access and peak travel times.","Refer a summary to the relevant public-works team."],
    "Safety & lighting":["Validate the location without publishing sensitive details.","Request a lighting inspection.","Track repair status; a report alone does not prove a crime."],
    "Health & accessibility":["Confirm service details with a qualified provider.","Avoid collecting medical details.","Document access barriers and check improvements."],
    "Education & internet":["Identify who is affected and what access is missing.","Explore shared access points or connectivity support.","Track reliability and access improvements."],
    "Food & housing":["Verify support needs respectfully without collecting names.","Use verified local service directories.","Track support gaps and service response."],
    "Environment":["Verify the location, date, and conditions.","Contact the relevant maintenance service.","Track follow-up observations."],
    "Other":["Clarify what happened, where, and who may be affected.","Identify a relevant service or community group.","Agree on a measurable next step."],
}
DEMO = [
{"Report ID":"DEMO-001","Issue":"Drinking water supply is irregular","Description":"Residents report that water has been unavailable for several days.","Area":"North Ward (illustrative)","Category":"Water & sanitation","People affected (estimate)":320,"Severity (1–5)":5,"Urgency (1–5)":5,"Priority score":96.0,"Priority":"Critical","Status":"Needs review","Latitude":16.5062,"Longitude":80.6480,"Reported at":"2026-10-26","Data source":"DEMO DATA — illustrative"},
{"Report ID":"DEMO-002","Issue":"Garbage collection was missed","Description":"Waste is accumulating near a local market.","Area":"Market Road (illustrative)","Category":"Waste management","People affected (estimate)":180,"Severity (1–5)":3,"Urgency (1–5)":3,"Priority score":55.0,"Priority":"Medium","Status":"Under review","Latitude":16.5150,"Longitude":80.6300,"Reported at":"2026-10-26","Data source":"DEMO DATA — illustrative"},
{"Report ID":"DEMO-003","Issue":"Street light near bus stop is broken","Description":"The road is dark after sunset and the walk feels unsafe.","Area":"College Junction (illustrative)","Category":"Safety & lighting","People affected (estimate)":95,"Severity (1–5)":4,"Urgency (1–5)":4,"Priority score":73.0,"Priority":"High","Status":"Needs review","Latitude":16.5200,"Longitude":80.6150,"Reported at":"2026-10-26","Data source":"DEMO DATA — illustrative"},
]
COLS = ["Report ID","Issue","Description","Area","Category","People affected (estimate)","Severity (1–5)","Urgency (1–5)","Priority score","Priority","Status","Evidence URL","Latitude","Longitude","Reported at","Data source","Submitted by"]

def get_config():
    try:
        return st.secrets["firebase"]["api_key"], st.secrets["firebase"].get("database_url", DB_DEFAULT).rstrip("/")
    except Exception:
        return None, DB_DEFAULT

def auth_call(endpoint, payload, api_key):
    r = requests.post(f"{AUTH_BASE}/{endpoint}?key={api_key}", json=payload, timeout=20)
    data = r.json()
    if not r.ok:
        msg = data.get("error", {}).get("message", "Authentication failed")
        friendly = {
            "EMAIL_EXISTS":"This email is already registered. Sign in instead.",
            "INVALID_LOGIN_CREDENTIALS":"Email or password is incorrect.",
            "EMAIL_NOT_FOUND":"Email or password is incorrect.",
            "INVALID_PASSWORD":"Email or password is incorrect.",
            "OPERATION_NOT_ALLOWED":"Enable Email/Password in Firebase Authentication.",
            "API_KEY_INVALID":"Firebase Web API key is incorrect. Check Streamlit Secrets.",
        }
        raise ValueError(friendly.get(msg, msg.replace("_"," ").title()))
    return data

def db(path, token, db_url, method="GET", payload=None):
    r = requests.request(method, f"{db_url}/{path.strip('/')}.json",
                         params={"auth":token}, json=payload, timeout=20)
    try: data = r.json()
    except Exception: data = None
    if not r.ok:
        if r.status_code in (401,403):
            raise ValueError("Firebase denied access. Check the Realtime Database rules.")
        raise ValueError(f"Database error ({r.status_code}). Check Firebase configuration.")
    return data

def classify(text):
    s = str(text).lower()
    scores = {cat:sum(term in s for term in terms) for cat,terms in CATS.items()}
    best = max(scores,key=scores.get)
    return best if scores[best] else "Other"

def priority(severity, urgency, people):
    sev=(severity-1)/4*100
    urg=(urgency-1)/4*100
    reach=min(100,math.log10(max(int(people),1)+1)/math.log10(10001)*100)
    n=round(.40*sev+.35*urg+.25*reach,1)
    return n, ("Critical" if n>=85 else "High" if n>=70 else "Medium" if n>=45 else "Low")

def get_reports(token, db_url):
    data=db("reports",token,db_url)
    rows=[]
    if isinstance(data,dict):
        for rid,row in data.items():
            if isinstance(row,dict):
                row.setdefault("Report ID",rid)
                rows.append(row)
    return pd.DataFrame(rows)

api_key, db_url = get_config()
with st.sidebar:
    st.markdown("## 🌱 CommunityConnect")
    st.caption("Community needs → clear next steps")
    if st.session_state.get("id_token"):
        st.success(st.session_state.get("email","Signed in"))
        if st.button("Sign out"):
            for k in ["id_token","refresh_token","email","uid"]:
                st.session_state.pop(k,None)
            st.rerun()

st.markdown('<div class="hero"><h1>CommunityConnect</h1><p>Collect local concerns, understand urgency, and explore practical next steps.</p></div>',unsafe_allow_html=True)
st.write("")
if not api_key:
    st.error("Add your Firebase Web API key to Streamlit Secrets first.")
    st.code(f'[firebase]\\napi_key = "PASTE_FIREBASE_WEB_API_KEY_HERE"\\ndatabase_url = "{DB_DEFAULT}"',language="toml")
    st.write("Find the Web API key in Firebase Console → Project settings → General → Your apps. Add a Web app if you do not have one. Do not put your service-account private key here.")
    st.stop()

if not st.session_state.get("id_token"):
    st.subheader("Sign in to CommunityConnect")
    tab1,tab2=st.tabs(["Sign in","Create account"])
    with tab1:
        with st.form("login"):
            email=st.text_input("Email")
            password=st.text_input("Password",type="password")
            submit=st.form_submit_button("Sign in",type="primary",use_container_width=True)
        if submit:
            try:
                d=auth_call("accounts:signInWithPassword",{"email":email.strip(),"password":password,"returnSecureToken":True},api_key)
                st.session_state.id_token=d["idToken"]; st.session_state.refresh_token=d.get("refreshToken",""); st.session_state.email=d.get("email",email); st.session_state.uid=d.get("localId","")
                st.rerun()
            except Exception as e: st.error(str(e))
    with tab2:
        with st.form("register"):
            new_email=st.text_input("Email address")
            p1=st.text_input("Password (minimum 6 characters)",type="password")
            p2=st.text_input("Confirm password",type="password")
            submit=st.form_submit_button("Create account",type="primary",use_container_width=True)
        if submit:
            if p1!=p2: st.error("Passwords do not match.")
            elif len(p1)<6: st.error("Password must contain at least 6 characters.")
            else:
                try:
                    d=auth_call("accounts:signUp",{"email":new_email.strip(),"password":p1,"returnSecureToken":True},api_key)
                    st.session_state.id_token=d["idToken"]; st.session_state.refresh_token=d.get("refreshToken",""); st.session_state.email=d.get("email",new_email); st.session_state.uid=d.get("localId","")
                    st.rerun()
                except Exception as e: st.error(str(e))
    st.info("This version implements email/password login. Google sign-in is not implemented in this Python login screen.")
    st.stop()

token=st.session_state.id_token
try:
    real=get_reports(token,db_url)
    if real.empty: reports=pd.DataFrame(DEMO)
    else:
        for c in COLS:
            if c not in real.columns: real[c]=None
        reports=pd.concat([pd.DataFrame(DEMO),real[COLS]],ignore_index=True)
except Exception as e:
    st.error(str(e))
    st.info("Database access is still locked or the database rules have not been configured. Follow the rules setup before testing submissions.")
    st.stop()

page=st.radio("Navigate",["Overview","Explore reports","Report a need","Opportunity finder","Map & locations","About"],horizontal=True,label_visibility="collapsed")
if page=="Overview":
    a,b,c,d=st.columns(4)
    a.metric("Reports shown",len(reports))
    b.metric("Critical / high",int(reports["Priority"].isin(["Critical","High"]).sum()))
    c.metric("Estimated people affected",f"{int(pd.to_numeric(reports['People affected (estimate)'],errors='coerce').fillna(0).sum()):,}")
    d.metric("Community submissions",int((reports["Data source"]=="Community submission").sum()))
    left,right=st.columns([1.1,1])
    with left:
        st.markdown("#### Issues needing attention")
        st.dataframe(reports.sort_values("Priority score",ascending=False)[["Issue","Area","Priority","Priority score","Status"]].head(7),use_container_width=True,hide_index=True)
    with right:
        st.markdown("#### Report categories")
        counts=reports["Category"].value_counts().rename_axis("Category").reset_index(name="Reports")
        fig=px.bar(counts,x="Reports",y="Category",orientation="h",color="Reports",color_continuous_scale=["#C8E6E0","#147D72"])
        fig.update_layout(height=340,margin=dict(l=0,r=5,t=5,b=0),coloraxis_showscale=False)
        st.plotly_chart(fig,use_container_width=True)
elif page=="Explore reports":
    st.subheader("Explore reports")
    cat=st.selectbox("Category",["All"]+sorted(reports["Category"].dropna().unique().tolist()))
    pr=st.selectbox("Priority",["All","Critical","High","Medium","Low"])
    q=st.text_input("Search issue or area")
    view=reports.copy()
    if cat!="All": view=view[view["Category"]==cat]
    if pr!="All": view=view[view["Priority"]==pr]
    if q: view=view[view[["Issue","Area","Description"]].fillna("").astype(str).apply(lambda x:x.str.contains(q,case=False,regex=False)).any(axis=1)]
    st.dataframe(view[[c for c in COLS if c in view.columns]].sort_values("Priority score",ascending=False),use_container_width=True,hide_index=True)
    st.download_button("Download CSV",view.to_csv(index=False).encode(), "communityconnect_reports.csv","text/csv")
elif page=="Report a need":
    st.subheader("Report a community need")
    st.warning("Do not include names, phone numbers, medical details, or other private information.")
    with st.form("report_form",clear_on_submit=True):
        title=st.text_input("What is the problem? *")
        desc=st.text_area("Describe what is happening *")
        area=st.text_input("Where is it happening? *")
        a,b,c=st.columns(3)
        people=a.number_input("Estimated people affected",1,1000000,50,10)
        sev=b.slider("Severity",1,5,3)
        urg=c.slider("Urgency",1,5,3)
        with st.expander("Optional location and evidence"):
            lat_s=st.text_input("Latitude")
            lon_s=st.text_input("Longitude")
            evidence=st.text_input("Evidence URL")
        submit=st.form_submit_button("Submit report",type="primary",use_container_width=True)
    if submit:
        if not title.strip() or not desc.strip() or not area.strip(): st.error("Fill in the problem, description, and location.")
        else:
            try:
                lat=lon=None
                if lat_s.strip() or lon_s.strip():
                    if not lat_s.strip() or not lon_s.strip(): raise ValueError("Enter both latitude and longitude, or leave both blank.")
                    lat=float(lat_s); lon=float(lon_s)
                    if not (-90<=lat<=90 and -180<=lon<=180): raise ValueError("Coordinates are out of range.")
                n,label=priority(sev,urg,people)
                rid="CC-"+uuid.uuid4().hex[:10].upper()
                row={"Report ID":rid,"Issue":title.strip(),"Description":desc.strip(),"Area":area.strip(),"Category":classify(title+" "+desc),"People affected (estimate)":int(people),"Severity (1–5)":int(sev),"Urgency (1–5)":int(urg),"Priority score":n,"Priority":label,"Status":"Needs review","Evidence URL":evidence.strip(),"Latitude":lat,"Longitude":lon,"Reported at":datetime.now(timezone.utc).isoformat(timespec="seconds"),"Data source":"Community submission","Submitted by":st.session_state.email,"Submitted by UID":st.session_state.uid}
                db("reports/"+rid,token,db_url,"PUT",row)
                st.success(f"Report saved to Firebase and shared! {label} priority · score {n}/100")
                st.rerun()
            except Exception as e: st.error(f"Could not save report: {e}")
elif page=="Opportunity finder":
    opts=reports.sort_values("Priority score",ascending=False)
    rid=st.selectbox("Choose an issue",opts["Report ID"].tolist(),format_func=lambda x:f"{opts.loc[opts['Report ID']==x,'Priority'].iloc[0]} · {opts.loc[opts['Report ID']==x,'Issue'].iloc[0]}")
    row=opts[opts["Report ID"]==rid].iloc[0]
    st.markdown(f"### {row['Issue']}")
    st.write(row["Description"])
    st.caption(f"{row['Area']} · {row['Category']}")
    st.metric("Priority score",f"{row['Priority score']}/100",row["Priority"])
    for i,action in enumerate(ACTIONS.get(row["Category"],ACTIONS["Other"]),1): st.markdown(f"**{i}.** {action}")
elif page=="Map & locations":
    pts=reports.dropna(subset=["Latitude","Longitude"]).copy()
    if not pts.empty:
        pts["latitude"]=pd.to_numeric(pts["Latitude"],errors="coerce"); pts["longitude"]=pd.to_numeric(pts["Longitude"],errors="coerce")
        pts=pts.dropna(subset=["latitude","longitude"])
        if not pts.empty: st.map(pts,latitude="latitude",longitude="longitude"); st.dataframe(pts[["Issue","Area","Priority","latitude","longitude"]],use_container_width=True,hide_index=True)
        else: st.info("No valid coordinates.")
    else: st.info("No reports have coordinates yet.")
else:
    st.markdown("""
### How it works
- Users sign in with email/password.
- Reports are saved in Firebase Realtime Database.
- Categories use keyword rules; priority combines severity (40%), urgency (35%), and estimated reach (25%).
- Demo reports are fictional and shown for illustration.
- Validate reports before taking action; scores are not automatic decisions.
""")
st.divider()
st.caption("CommunityConnect · Hackathon prototype · Human review required")
