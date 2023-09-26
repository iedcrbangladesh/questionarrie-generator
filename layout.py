#!/usr/bin/python
import psycopg2
from psycopg2.extras import RealDictCursor

from config import config
import sys
import os
import time
import re
import errno
import json


STRUCUTRE_PATH = os.path.join(os.path.sep,'structures','templates')

def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
		
        # create a cursor
        cur = conn.cursor()
        
	# execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')

        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)

        #domload(cur, id)
       
	# close the communication with the PostgreSQL
        #cur.close()
        #return cur
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            #conn.close()
            #print('Database connection closed.')
            return conn
    #return conn


    

def create_layout(title,dirname,gen_path,initialFormValues, sectionLink="[]"):
    filepath = os.path.join(os.path.sep,gen_path,'dashboard',dirname)
    filename = os.path.join(os.path.sep,filepath,'layout.tsx')    
    code = r'''"use client";
import { ReactNode, useEffect, useState, useCallback } from 'react';
import {Formik, Form, yupToFormErrors, validateYupSchema, useFormikContext} from 'formik';
import { useRouter } from "next/navigation";
import axios from 'axios';

import Header from '@/app/components/Header';
import Sidebar from '@/app/components/Sidebar';
import useAuth from '@/app/hooks/useAuth';
import SectionLink from '@/app/components/SectionLink';

const url = process.env.api_url;

import '''+title+'''Schema from '@/app/utils/'''+title+'''Schema';


interface '''+title+'''LayoutProps {
  children: ReactNode;
}

const FormObserver =() => {
  const { values } = useFormikContext();

  useEffect(() => {
    console.log("FormObserver::values", values);
    if(typeof window !== 'undefined'){
      localStorage.setItem('data',JSON.stringify(values));
    }
  }, [values]);

  return null;
};

const '''+title+'''Layout = ({ children }: '''+title+'''LayoutProps) => {
  const router = useRouter();  
  const authCtx = useAuth();
  const userid = authCtx.userId;
  const mobileNumber = authCtx.activeMobileNumber;
  const contactId = authCtx.activeContactId;

  const [sidebarOpen, setSidebarOpen] = useState(false);

  let '''+title+''' ={
    '''+initialFormValues+'''
  };

  const sectionLink:any = '''+sectionLink+''';

  const fetch'''+title+'''Data = useCallback(async()=>{
    const response = await axios.get(`${url}get-question/${contactId}`);
    if(typeof window !== 'undefined' && response.data.data!=null){
      localStorage.setItem('data',JSON.stringify(response.data.data));
    }
  },[contactId]);

  useEffect(()=>{
    fetch'''+title+'''Data();      
  },[fetch'''+title+'''Data]);

  let previous_data = typeof window !== 'undefined'?localStorage.getItem('data'):null;

  if(previous_data!=null && typeof window !== 'undefined'){
    //console.log(JSON.parse(previous_data))
    '''+title+''' = JSON.parse(previous_data)
  }

  const handleFormSubmit = async(values:any)=>{
    //console.log(values);
    await axios.post(`${url}save-question`, 
    {
    userid:authCtx.userId,
    data:values,
    contactnumber:mobileNumber,
    done:1
    }, 
    {    
      headers: {
        'Content-Type': 'application/json'
      }
    }
    ) .then(function (response:any) {

      if(typeof window !== 'undefined' && response.data.contact_question_id){
            localStorage.removeItem('data');
            authCtx.activeMobileNumber = null;
            authCtx.selectedMobile(null);
            localStorage.removeItem("MobileNumber")

            localStorage.removeItem("ContactID")
            authCtx.activeContactId = null;
            authCtx.selectedContactId(null);
                                                
            //remove skip rules
            authCtx.redirect =null;
            authCtx.setRedirect(null);
            authCtx.focusElement = null;
            authCtx.setFocusElement(null);

            localStorage.removeItem("redirect")
            localStorage.removeItem('focusElement');
      }
      router.push('/dashboard/callinterface')

    })

    

  }

  return (
    <div className="dark:bg-boxdark-2 dark:text-bodydark">
      {/* <!-- ===== Page Wrapper Start ===== --> */}
      <div className="flex h-screen overflow-hidden bg-slate-800">
        {/* <!-- ===== Sidebar Start ===== --> */}
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
        {/* <!-- ===== Sidebar End ===== --> */}

        {/* <!-- ===== Content Area Start ===== --> */}
        <div className="relative flex flex-1 flex-col overflow-y-auto overflow-x-hidden">
          {/* <!-- ===== Header Start ===== --> */}
          <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
          {/* <!-- ===== Header End ===== --> */}

          {/* <!-- ===== Main Content Start ===== --> */}
          <main>
            <div className="mx-auto max-w-screen-2xl p-1 md:p-2 2xl:p-10">
              <SectionLink linkdata={sectionLink}/>
              <Formik 
              initialValues={'''+title+'''}
              validationSchema={'''+title+'''Schema} 
              onSubmit={handleFormSubmit}>              
                <Form className='mt-2 rounded-md border border-stroke p-2 py-1 dark:border-strokedark sm:py-2.5 sm:px-2 xl:px-2.5'>
                    <FormObserver />
                    {children}
                </Form>
              </Formik>
              
            </div>
          </main>
          {/* <!-- ===== Main Content End ===== --> */}
        </div>
        {/* <!-- ===== Content Area End ===== --> */}
      </div>
      {/* <!-- ===== Page Wrapper End ===== --> */}
    </div>
  );
};

export default '''+title+'''Layout;
'''
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

def initial_FormValues(cur,id):
  initialFormValues = ''
  option_data = '{'
  validation_rules = r'''import { object, array, string, number, StringSchema } from "yup";
    export default object().shape({
    '''
  sectionLink = "[\n"
  disabled_rules = '{'
  skip_logic = '{'

  cur.execute('select *from section where questionnaire_id = %s order by section_order asc',(id))
  sections  = cur.fetchall()
  for section in sections:
    
    section_id = int(section['id'])
    cur.execute('select *from question where section_id = %s order by question_order asc',(section_id,))
    questions = cur.fetchall()
    
    
    if(questions):
        validation_rules+=section['slug']+':object().shape({\n'
        option_data +='"'+section['slug']+'":{\n'
        sectionLink+='{"label":"'+section['label']+'","href":"'+section['slug']+'"},\n'
        initialFormValues+=section['slug']+':{\n'
        for row in questions:
          #disabled logic
          if(row['disabled_rules']!=None):
            disabled_rules+='"'+section['slug']+'.'+row['variable']+'":'+row['disabled_rules']+',\n'
          #end disabled logic

          #skip logic
          if(row['skip_logic']!=None):
            skip_logic+='"'+section['slug']+'.'+row['variable']+'":\n'+row['skip_logic']+',\n'
          #end skip logic

          if(row['validation_rules']!=None and len(row['validation_rules']) > 2 ):
            rules = row['validation_rules'].replace("[this]",row['error_label'])
            validation_rules+=''+row['variable']+':'+rules+',\n'

          #initial value
          if(row['type'] =='number'):
            initialFormValues+=row['variable']+':0,\n'
          if(row['type'] =='text'):
            initialFormValues+=row['variable']+':"",\n'

          if(row['type'] =='hour_minutes'):
            initialFormValues+=row['variable']+':{hour:0, minute:0},\n'  

          if(row['type'] =='text_radio'):
            initialFormValues+=row['variable']+':{text:\'\',reason:{value:\'\',label:\'\'}},\n'
          
          if(row['type'] =='man_women_count'):
            initialFormValues+=row['variable']+':{man:\'\',women:\'\'},\n'
              
          if(row['type'] in {'dropdown','radio','age_dropdown'}):
            initialFormValues+=row['variable']+':{value:\'\',label:\'\'},\n'    
          if(row['type'] =='checkbox' or row['type'] =='multiselect'):
            initialFormValues+=row['variable']+':[],\n'

          if(row['type'] in {'district_dropdown','citycorporation_dropdown','upazilla_dropdown','municipality_dropdown'}):
            initialFormValues+=row['variable']+':{value:\'\',label:\'\',parent:\'\'},\n'



          #options
          list_options = {'radio','checkbox', 'multiselect', 'dropdown','text_radio'}

          if(row['type'] in list_options and row['options'] is not None):
            option_data+='"'+row['variable']+'":'+row['options']+',\n'

          if(row['type'] == 'age_dropdown' and row['custom_attributes']!=None):
            age_start,age_end = 0,0            
            custom_attributes = json.loads(row['custom_attributes'])                        
            for c_a in custom_attributes:                                               
                age_start = int(c_a['value']) if c_a['label']=='start' else 0
                age_end = int(c_a['value']) if c_a['label']=='end' else 0                            
            if(age_start >=0  and age_end < 200):              
              age_list = list()
              age_range = range(age_start,age_end+1)               
              for ar in age_range:
                age_list.append({'value':ar,'label':f"{ar}"})              
              if(row['options']!=None):
                age_extra_options = json.loads(row['options'])
                age_list.extend(age_extra_options)
            option_data+='"'+row['variable']+'":'+json.dumps(age_list,ensure_ascii=False)+',\n'
        pos_occurance = option_data.rfind(',')
        option_data = option_data[:pos_occurance] + ' ' + option_data[pos_occurance+1:]    
        initialFormValues+='},\n'
        option_data += '}, \n'
        validation_rules += r'''
        }),
        '''
    
    if(section['type']>0):
      sectionLink+='{"label":"'+section['label']+'","href":"'+section['slug']+'"},\n'
      
      
  sectionLink+="]"
  option_data += '}'
  validation_rules += r'''
    });
    '''
  disabled_rules += '}'

  skip_logic+= '}'

  pos_occurance = option_data.rfind(',')
    #pos_occurance_rules = validation_rules.rfind(',')
  option_data = option_data[:pos_occurance] + ' ' + option_data[pos_occurance+1:]

  pos_occurance_dr = disabled_rules.rfind(',')
    #pos_occurance_rules = validation_rules.rfind(',')
  disabled_rules = disabled_rules[:pos_occurance_dr] + ' ' + disabled_rules[pos_occurance_dr+1:]
  
  pos_occurance_sl = skip_logic.rfind(',')
    #pos_occurance_rules = validation_rules.rfind(',')
  skip_logic = skip_logic[:pos_occurance_sl] + ' ' + skip_logic[pos_occurance_sl+1:]
  
  return (initialFormValues,
    option_data,
    validation_rules,
    sectionLink, 
    disabled_rules,
    skip_logic
    )  


def create_component (cur,id,gen_path):
    cur.execute('select *from questionnaire where id = %s limit 1',(id))
    data  = cur.fetchone()
    title = re.sub('[^A-Za-z]+', '', data['title']).lower()    
    filepath = os.path.join(os.path.sep,gen_path,'dashboard',title)
    filename = os.path.join(os.path.sep,filepath,'page.tsx')
    if not os.path.exists(filepath):
        try:
           os.mkdir(filepath) 
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    component_name = title.capitalize()

    return (component_name, filename,title)


def create_disabled_rules(title,gen_path,disabled_rules):
  filepath = os.path.join(os.path.sep,gen_path,'json')
  filename = os.path.join(os.path.sep,filepath,'disablelogic.json')
  if not os.path.exists(filepath):
      try:
        os.mkdir(filepath) 
      except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
          raise
  with open(filename, "w",encoding="utf-8") as f:
        f.write(disabled_rules)

def create_skip_logic(title,gen_path,skip_rules):
  filepath = os.path.join(os.path.sep,gen_path,'json')
  filename = os.path.join(os.path.sep,filepath,'skiplogic.json')
  if not os.path.exists(filepath):
      try:
        os.mkdir(filepath) 
      except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
          raise
  with open(filename, "w",encoding="utf-8") as f:
        f.write(skip_rules)


def create_option_data(title,gen_path,option_data):
  filepath = os.path.join(os.path.sep,gen_path,'json')
  filename = os.path.join(os.path.sep,filepath,title+'_data.json')
  if not os.path.exists(filepath):
      try:
        os.mkdir(filepath) 
      except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
          raise
  with open(filename, "w",encoding="utf-8") as f:
        f.write(option_data)


def create_validation_schema(gen_path, title, validation_ruels):
    filepath = os.path.join(os.path.sep,gen_path,'utils')
    filename = os.path.join(os.path.sep,filepath,title+'Schema.ts')
    if not os.path.exists(filepath):
      try:
        os.mkdir(filepath) 
      except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
          raise
    with open(filename, "w",encoding="utf-8") as f:
        f.write(validation_ruels)

def demo_data(type_id, filename):
  
  option_data = '[\n'
  cur.execute("select *from areas where area_type = %s",(type_id,))
  datas =  cur.fetchall()
  for row in datas:
    bangla_name = row['bangla_name'] if row['bangla_name'] != None else ""
    #print(type(bangla_name))
    name = row['name'] if row['name'] != None else ""

    option_data+='{"label":"'+(name)+' '+(bangla_name)+' ", "value":'+str(row['area_code'])+',"parent":'+str(row['parent_code'])+'},\n'

  option_data +=']'
  pos_occurance = option_data.rfind(',')
  option_data = option_data[:pos_occurance] + ' ' + option_data[pos_occurance+1:]

  filepath = os.path.join(os.path.sep,gen_path,'json')
  filename = os.path.join(os.path.sep,filepath,filename+'.json')

  with open(filename, "w",encoding="utf-8") as f:
        f.write(option_data)

def create_demographics_data(gen_path,cur,id):
    
  cur.execute("select *from question where questionnaire_id = %s and type in ('district_dropdown','citycorporation_dropdown','upazilla_dropdown','municipality_dropdown') ",(id,))
  questions = cur.fetchall()
  if(questions):
    for row in questions:
      #print(row['type'])
      filename = row['type'].replace("_dropdown","")
      if(row['type'] == 'district_dropdown'):
        demo_data(5, filename)
        time.sleep(1)

      if(row['type'] == 'upazilla_dropdown'):
        demo_data(6, filename)
        time.sleep(1)

      if(row['type'] == 'citycorporation_dropdown'):
        demo_data(7, filename)
        time.sleep(1)

      if(row['type'] == 'municipality_dropdown'):
        demo_data(9, filename)
        time.sleep(1)
  '''
  filename = os.path.join(os.path.sep,filepath,'_data.json')
  if not os.path.exists(filepath):
      try:
        os.mkdir(filepath) 
      except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
          raise
  with open(filename, "w",encoding="utf-8") as f:
        f.write(option_data)  

  '''
if __name__ == '__main__':
    id = sys.argv[1]
    gen_path = sys.argv[3]
    action = sys.argv[2]
    conn = connect()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    component = create_component (cur,id,gen_path)
    component_name = component[0]
    component_file = component[1]
    title = component[2]
    
    domdata = initial_FormValues(cur,id)
    init_form_values =   domdata[0]
    option_data = domdata[1]
    validation_rules = domdata[2]
    sectionLink = domdata[3]
    disabled_rules = domdata[4]
    skip_logic = domdata[5]
    
    if(action == 'dl'):
      create_disabled_rules(title,gen_path,disabled_rules)
    if(action == 'sl'):
      create_skip_logic(title,gen_path,skip_logic)
    if(action == 'od'):
      create_option_data(title,gen_path,option_data)
    if(action == 'vs'):
      create_validation_schema(gen_path, component_name, validation_rules)
    if(action == 'layout'):
      create_layout(component_name,title, gen_path, init_form_values, sectionLink)
    if(action == 'demograph'):
      create_demographics_data(gen_path,cur,id)
    
    cur.close()
    conn.close()
