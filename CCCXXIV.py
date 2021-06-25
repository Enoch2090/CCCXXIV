import streamlit as st
import pandas as pd
import os
import sys
import time
import json
import base64
import pickle
import shutil
import random
import hashlib

ADD_NEW_SOURCE = "Add a new Source"
CACHE = "cache"
CACHE_THRESH = 5
CACHE_EXPIRE_TIME = 900
DEFAULT_SOURCE = f"{CACHE}/source.pkl"
DEFAULT_SUBMISSION = f"{CACHE}/submission.pkl"

get_time = lambda x: time.strptime(x.split("_")[1], '%Y-%m-%d-%H-%M-%S')

def check_file_expiration(file_list):
    curr_time = time.mktime(time.localtime())
    file_all_expired = all([(curr_time-time.mktime(get_time(file_name)))>CACHE_EXPIRE_TIME for file_name in file_list])
    return file_all_expired

def get_source():
    source_files = [
        os.path.join(CACHE, x) for x in os.listdir(CACHE) if "source_" in x
    ]
    with open(DEFAULT_SOURCE, "rb") as f:
        source_df = pickle.load(f)
    for source_file in source_files:
        with open(source_file, "rb") as f:
            source_df_cache = pickle.load(f)
        source_df = pd.merge(source_df, source_df_cache, how="outer")
    # source_df["URL"] = source_df["URL"].apply(lambda x: f'<a target="_blank" href="{x}">{x}</a>')
    if len(source_files) > CACHE_THRESH and check_file_expiration(source_files):
        with open(DEFAULT_SOURCE, "wb") as f:
            pickle.dump(source_df, f)        
    return source_df

def get_submission():
    submission_files = [
        os.path.join(CACHE, x) for x in os.listdir(CACHE) if "submission_" in x
    ]
    with open(DEFAULT_SUBMISSION, "rb") as f:
        submission_df = pickle.load(f)
    for submission_file in submission_files:
        with open(submission_file, "rb") as f:
            submission_df_cache = pickle.load(f)
        submission_df = pd.merge(submission_df, submission_df_cache, how="outer")
    submission_df["Time"] = submission_df["Time"].apply(lambda x: time.strftime("%Y/%m/%d %H:%M", x))
    if len(submission_files) > CACHE_THRESH and check_file_expiration(submission_files):
        with open(DEFAULT_SUBMISSION, "wb") as f:
            pickle.dump(submission_df, f) 
    return submission_df

# ----------------Functionalities----------------
def cccxxiv_submission(sources, submissions):
    st.title('Submission')
    location = st.multiselect(
        label="Source",
        options=sources["Name"].tolist()+[ADD_NEW_SOURCE]
    )
    source_name = ""
    source_url = ""
    poem = ""
    name = ""
    stu_id = ""
    if ADD_NEW_SOURCE in location:
        source_name = st.text_input("Source Name")
        source_url = st.text_input("Source URL")
    poem = st.text_input("Your Poem Title")
    name = st.text_input("Your Name")
    stu_id = st.text_input("Your Student ID")

    if st.button("Done"):
        submission_time = time.localtime()
        random.seed(submission_time)
        submission_strftime = time.strftime("%Y-%m-%d-%H-%M-%S", submission_time)
        submission_identifier = f"{submission_time}_{random.randint(0, 99999)}_{name}"
        submission_id = str(int(hashlib.sha1(submission_identifier.encode("utf-8")).hexdigest(), 16) % (10 ** 8))
        input_valid = check_inputs(poem, name, stu_id, source_name, source_url, location, submission_id)
        if not input_valid:
            return
        submission_content = [
            {
                "Name": name, 
                "Student ID": stu_id,
                "Location": ", ".join(location) if ADD_NEW_SOURCE not in location else ", ".join([x for x in location if x != ADD_NEW_SOURCE]+[source_name]),
                "Poem": poem,
                "Time": submission_time
            } 
        ]
        with open(f"{CACHE}/submission_{submission_strftime}_{submission_id}.pkl", "wb") as f:
            pickle.dump(pd.DataFrame(submission_content), f)
        if ADD_NEW_SOURCE not in location:
            return
        source_content = [
            {
                "Name": source_name, 
                "URL": source_url
            }
        ]
        with open(f"{CACHE}/source_{submission_strftime}_{submission_id}.pkl", "wb") as f:
            pickle.dump(pd.DataFrame(source_content), f)

def cccxxiv_del_submission():
    st.markdown("## I want to delete a submission")
    st.markdown("This function should only be used when there is a typo. Don't abuse it!")
    del_submission_id = ""
    del_submission_id = st.text_input("Enter the ID of that submission")
    if st.button("Delete"):
        if del_submission_id == "":
            st.error("Please enter a submission id")
            return
        if not any([del_submission_id in x for x in os.listdir(CACHE)]):
            st.error("Submission id not found")
            return
        for submission_file in [x for x in os.listdir(CACHE) if del_submission_id in x]:
            os.remove(os.path.join(CACHE, submission_file))
        st.info("Successfully removed submission")
        return

def cccxxiv_records(sources, submissions):
    st.markdown("## Sources to submit:")
    st.table(sources)
    # st.write(sources.to_html(escape=False), unsafe_allow_html=True)
    st.markdown("## Records of your classmates:")
    st.table(submissions)
    # st.write(submissions.to_html(escape=False), unsafe_allow_html=True)

def cccxxiv_help():
    with open('help.md', 'r') as f:
        helper = "".join(f.readlines())
    st.markdown(helper)

def check_inputs(poem, name, stu_id, source_name, source_url, location, submission_id):
    if poem == "":
        st.error("Poem name is empty")
        return False
    if name == "":
        st.error("Your name is empty")
        return False
    if stu_id == "":
        st.error("Student ID is empty")
        return Falsez
    if len(stu_id) != 12 and stu_id[0] != "5":
        st.error("Wrong format of student ID")
        return False
    if ADD_NEW_SOURCE in location and source_name == "":
        st.error("Need to input new source name")
        return False
    if ADD_NEW_SOURCE in location and source_url == "":
        st.error("Need to input new source url")
        return False
    st.info(f"Submission complete, ID for this submission is {submission_id}. You will need this ID if you wish to delete this entry.")
    return True

# ----------------Menu----------------
sources = get_source()
submissions = get_submission()
st.sidebar.title('CCCXXIV')
option = st.sidebar.selectbox(
    'Menu',
    ['Submission', 'Records', 'Delete', 'Help'])
if option == 'Submission':
    cccxxiv_submission(sources, submissions)
elif option == 'Records':
    cccxxiv_records(sources, submissions)
elif option == 'Delete':
    cccxxiv_del_submission()
elif option == 'Help':
    cccxxiv_help()


# ----------------Hide Development Menu----------------
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)
