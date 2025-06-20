import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
# ---------------------
# Firebase 설정
# ---------------------
cred = credentials.Certificate("serviceAccountKey.json")

# ✅ 딕셔너리(firebase_config)가 아니라 `cred`를 넘겨야 함
firebase_admin.initialize_app(cred, {
    'storageBucket': 'your-project-id.appspot.com'
})

firebase = firebase_admin.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("population_trends.csv")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded, parse_dates=['datetime'])

        tabs = st.tabs([
            "1. 기초 통계",
            "2. 연도별 추이"
            "3. 지역별분석" 
            "4. 변화량 분석" 
            "5. 시각화"
        ])

        # 1. 목적 & 분석 절차
        st.title("🧹 인구 데이터 전처리")

        uploaded_file = st.file_uploader("population_trends.csv 업로드", type="csv")

        if uploaded_file:
            df = pd.read_csv(uploaded_file)

            st.subheader("📍 원본 데이터 일부 미리보기")
            st.dataframe(df.head())

            # 🔧 '세종' 지역의 '-' 값 → 0
            df_sejong = df[df['지역'] == '세종'].replace('-', 0)

            # 원래 df에서 세종 데이터만 바꾸기
            df.update(df_sejong)

            # 🔢 숫자형으로 변환할 열
            num_cols = ['인구', '출생아수(명)', '사망자수(명)']
            for col in num_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')  # 숫자로 변환 (에러는 NaN 처리)

            st.subheader("📊 데이터 요약 통계 (`describe()`)")
            st.dataframe(df.describe())

            st.subheader("🔎 데이터 구조 (`info()`)")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

        else:
            st.info("CSV 파일을 업로드해 주세요.")

        # 2. 데이터셋 설명
        st.title("📈 National Population Trend Forecast")

        uploaded_file = st.file_uploader("Upload population_trends.csv", type="csv")

        if uploaded_file:
            df = pd.read_csv(uploaded_file)

            # Convert columns
            df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].apply(pd.to_numeric, errors='coerce')

            # Filter nationwide data
            df_nat = df[df['지역'] == '전국'].copy()

            # Sort by year
            df_nat = df_nat.sort_values('연도')

            # Plot population trend
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.lineplot(x='연도', y='인구', data=df_nat, marker='o', ax=ax)
            ax.set_title("National Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")

            # Predict 2035 population
            recent_years = df_nat['연도'].max()
            df_recent = df_nat[df_nat['연도'] >= recent_years - 2]  # 최근 3년

            avg_birth = df_recent['출생아수(명)'].mean()
            avg_death = df_recent['사망자수(명)'].mean()

            latest_pop = df_nat[df_nat['연도'] == recent_years]['인구'].values[0]
            predicted_2035 = latest_pop + (avg_birth - avg_death) * (2035 - recent_years)

            # 표시
            ax.axhline(predicted_2035, ls='--', color='red')
            ax.text(2035, predicted_2035, f'2035 est: {int(predicted_2035):,}', color='red')
            ax.set_xlim(df_nat['연도'].min(), 2036)

            st.pyplot(fig)

            # 수치 출력
            st.markdown(f"""
                🔢 **Latest year**: {recent_years}  
                👶 Average births (3yr): {avg_birth:,.0f}  
                ⚰️ Average deaths (3yr): {avg_death:,.0f}  
                📊 **Predicted population in 2035**: `{int(predicted_2035):,}` people
            """)
        else:
            st.info("Please upload the population_trends.csv file.")

        # 3. 데이터 로드 & 품질 체크
        import streamlit as st
        import pandas as pd
        import seaborn as sns
        import matplotlib.pyplot as plt

        st.title("📊 Regional Population Change (5-Year)")

        uploaded_file = st.file_uploader("Upload population_trends.csv", type="csv")

        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            df[['인구']] = df[['인구']].apply(pd.to_numeric, errors='coerce')

            # 최근 5년 데이터 필터링
            latest_year = df['연도'].max()
            df_recent = df[df['연도'].between(latest_year - 5, latest_year)]

            # 지역별 피벗: index=지역, columns=연도, values=인구
            df_pivot = df_recent.pivot(index='지역', columns='연도', values='인구')

            # 변화량 계산
            df_pivot['Change'] = df_pivot[latest_year] - df_pivot[latest_year - 5]
            df_pivot['Change(%)'] = (df_pivot['Change'] / df_pivot[latest_year - 5]) * 100

            # '전국' 제외
            df_change = df_pivot.drop(index='전국')

            # 영문 지역명 매핑 (예시, 필요한 경우 확장 가능)
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
                '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi',
                '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk',
                '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam', '제주': 'Jeju'
            }
            df_change['Region'] = df_change.index.map(region_map)

            # 변화량 그래프 (천명 단위)
            df_sorted = df_change.sort_values('Change', ascending=False)
            df_sorted['Change_thousand'] = df_sorted['Change'] / 1000

            st.subheader("📈 Population Change (Last 5 Years)")
            fig1, ax1 = plt.subplots(figsize=(8, 6))
            sns.barplot(x='Change_thousand', y='Region', data=df_sorted, ax=ax1, palette="viridis")
            ax1.set_title("Population Change (Thousand)")
            ax1.set_xlabel("Change (Thousands)")
            ax1.set_ylabel("Region")
            for i, value in enumerate(df_sorted['Change_thousand']):
                ax1.text(value, i, f"{value:,.1f}", va='center', ha='left')
            st.pyplot(fig1)

            st.markdown(
                "> 🧾 **Interpretation**: The graph shows total population increase/decrease per region over the past 5 years. Positive values indicate growth, negative values indicate decline.")

            # 변화율 그래프
            df_sorted_rate = df_sorted.sort_values('Change(%)', ascending=False)

            st.subheader("📉 Population Change Rate (%)")
            fig2, ax2 = plt.subplots(figsize=(8, 6))
            sns.barplot(x='Change(%)', y='Region', data=df_sorted_rate, ax=ax2, palette="coolwarm")
            ax2.set_title("Population Growth Rate (%)")
            ax2.set_xlabel("Change Rate (%)")
            ax2.set_ylabel("Region")
            for i, value in enumerate(df_sorted_rate['Change(%)']):
                ax2.text(value, i, f"{value:.1f}%", va='center', ha='left')
            st.pyplot(fig2)

            st.markdown(
                "> 🧾 **Interpretation**: This chart shows relative change rate compared to 5 years ago. Smaller regions may have large percentage swings even with small absolute changes.")
        else:
            st.info("Please upload the population_trends.csv file.")

        # 4. Datetime 특성 추출
        import streamlit as st
        import pandas as pd
        import numpy as np

        st.title("📌 Top 100 Population Changes (Yearly Diff)")

        uploaded_file = st.file_uploader("Upload population_trends.csv", type="csv")

        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce')

            # 전국 제외
            df = df[df['지역'] != '전국'].copy()

            # 연도별 차이 계산
            df_sorted = df.sort_values(['지역', '연도'])
            df_sorted['증감'] = df_sorted.groupby('지역')['인구'].diff()

            # 증감 기준 상위 100개
            top_changes = df_sorted.dropna(subset=['증감']).copy()
            top_100 = top_changes.sort_values('증감', ascending=False).head(100)

            # 천단위 콤마 표시용 포맷
            def format_number(x):
                return f"{int(x):,}"

            # 컬러바 스타일링 함수
            def highlight_diff(val):
                if pd.isna(val):
                    return ''
                color = '#d6eaff' if val > 0 else '#ffe5e5'  # 파랑(증가) / 빨강(감소)
                return f'background-color: {color}'

            # 포맷 및 스타일 적용
            styled_df = top_100[['연도', '지역', '인구', '증감']].copy()
            styled_df['인구'] = styled_df['인구'].apply(format_number)
            styled_df['증감'] = styled_df['증감'].apply(format_number)

            st.subheader("🔝 Top 100 Yearly Changes by Region")
            st.dataframe(
                styled_df.style.applymap(highlight_diff, subset=['증감'])
            )

            st.markdown(
                "> 📌 **Interpretation**: These are the top 100 biggest population changes across all regions and years (excluding national total). Blue = growth, Red = decline.")
        else:
            st.info("Please upload the population_trends.csv file.")

        # 5. 시각화
        import streamlit as st
        import pandas as pd
        import matplotlib.pyplot as plt

        st.title("📊 Stacked Area Chart by Region (Population Over Years)")

        uploaded_file = st.file_uploader("Upload population_trends.csv", type="csv")

        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce')

            # '전국' 제외
            df = df[df['지역'] != '전국']

            # 지역명 영어 변환 (예시: 수정 가능)
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }
            df['Region'] = df['지역'].map(region_map)

            # 피벗 테이블 생성: index=연도, columns=지역(영문), values=인구
            pivot_df = df.pivot_table(index='연도', columns='Region', values='인구', aggfunc='sum')
            pivot_df = pivot_df.fillna(0)  # 결측치는 0으로

            # 누적 영역 그래프 그리기
            fig, ax = plt.subplots(figsize=(10, 6))
            pivot_df.plot.area(ax=ax, cmap='tab20')  # 색상 팔레트

            ax.set_title("Stacked Area Chart of Population by Region")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(title="Region", loc='upper left', bbox_to_anchor=(1, 1))

            st.pyplot(fig)

            st.markdown(
                "> 📌 **Interpretation**: The stacked area chart shows how each region contributes to the overall population across years. Color-coded areas help distinguish trends by region.")
        else:
            st.info("Please upload the population_trends.csv file.")



        st.set_page_config(page_title="Population EDA", layout="wide")
        st.title("📊 Population Trend EDA App")

        uploaded_file = st.file_uploader("📁 Upload population_trends.csv", type="csv")

        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            df.replace('-', 0, inplace=True)
            df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].apply(pd.to_numeric)

            tabs = st.tabs(["📌 기초 통계", "📈 연도별 추이", "📊 지역별 분석", "📉 변화량 분석", "📍 시각화"])

            # ───────────────────────────────────────────────
            with tabs[0]:  # 기초 통계
                st.header("📌 Basic Statistics")
                st.subheader("ℹ️ Data Info")
                buf = io.StringIO()
                df.info(buf=buf)
                st.text(buf.getvalue())

                st.subheader("📊 Descriptive Statistics")
                st.dataframe(df.describe())

                st.subheader("🔍 Missing Values")
                st.dataframe(df.isnull().sum())

                st.subheader("📋 Sample Data")
                st.dataframe(df.head())

            # ───────────────────────────────────────────────
            with tabs[1]:  # 연도별 추이
                st.header("📈 National Population Trend")
                df_nat = df[df['지역'] == '전국'].sort_values('연도')
                fig, ax = plt.subplots()
                sns.lineplot(x='연도', y='인구', data=df_nat, marker='o', ax=ax)
                ax.set_title("National Population Trend")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")

                # 2035 예측
                recent = df_nat[df_nat['연도'] >= df_nat['연도'].max() - 2]
                avg_birth = recent['출생아수(명)'].mean()
                avg_death = recent['사망자수(명)'].mean()
                last_pop = df_nat[df_nat['연도'] == df_nat['연도'].max()]['인구'].values[0]
                pred_2035 = last_pop + (avg_birth - avg_death) * (2035 - df_nat['연도'].max())

                ax.axhline(pred_2035, ls='--', color='red')
                ax.text(2035, pred_2035, f'2035 est: {int(pred_2035):,}', color='red')
                ax.set_xlim(df_nat['연도'].min(), 2036)
                st.pyplot(fig)
                st.markdown(f"🔮 Predicted population in 2035: **{int(pred_2035):,}**")

            # ───────────────────────────────────────────────
            with tabs[2]:  # 지역별 분석
                st.header("📊 Regional Change (5 Years)")
                latest = df['연도'].max()
                recent = df[df['연도'].between(latest - 5, latest)]
                pivot = recent.pivot(index='지역', columns='연도', values='인구')
                pivot['Change'] = pivot[latest] - pivot[latest - 5]
                pivot = pivot.drop('전국').sort_values('Change', ascending=False)
                pivot['Change_thousand'] = pivot['Change'] / 1000

                fig2, ax2 = plt.subplots()
                sns.barplot(x='Change_thousand', y=pivot.index, data=pivot.reset_index(), ax=ax2)
                ax2.set_title("5-Year Population Change by Region")
                ax2.set_xlabel("Change (Thousands)")
                st.pyplot(fig2)

            # ───────────────────────────────────────────────
            with tabs[3]:  # 변화량 분석
                st.header("📉 Top 100 Yearly Differences")
                df = df[df['지역'] != '전국']
                df = df.sort_values(['지역', '연도'])
                df['증감'] = df.groupby('지역')['인구'].diff()
                top100 = df.dropna().sort_values('증감', ascending=False).head(100)

                def format_color(val):
                    color = '#d0f0ff' if val > 0 else '#ffe0e0'
                    return f'background-color: {color}'

                table = top100[['연도', '지역', '인구', '증감']].copy()
                table['인구'] = table['인구'].apply(lambda x: f"{int(x):,}")
                table['증감'] = table['증감'].apply(lambda x: f"{int(x):,}")
                st.dataframe(table.style.applymap(format_color, subset=['증감']))

            # ───────────────────────────────────────────────
            with tabs[4]:  # 시각화
                st.header("📍 Stacked Area Chart by Region")
                region_map = {
                    '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                    '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                    '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                    '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                    '제주': 'Jeju'
                }
                df['Region'] = df['지역'].map(region_map)
                pivot_area = df[df['지역'] != '전국'].pivot_table(index='연도', columns='Region', values='인구',
                                                              aggfunc='sum').fillna(0)
                fig3, ax3 = plt.subplots(figsize=(10, 6))
                pivot_area.plot.area(ax=ax3, cmap='tab20')
                ax3.set_title("Stacked Area Population by Region")
                ax3.set_xlabel("Year")
                ax3.set_ylabel("Population")
                ax3.legend(title="Region", bbox_to_anchor=(1, 1))
                st.pyplot(fig3)

        else:
            st.info("📥 Please upload the population_trends.csv file.")


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()