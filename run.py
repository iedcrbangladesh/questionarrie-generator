#!/usr/bin/python
import psycopg2
from psycopg2.extras import RealDictCursor

from config import config
import sys
import os
import time
import re
import errno


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


def create_questionarie(component_name, filename, question_template):
    code = r'''"use client";
//Library
import Link from "next/link";
import RadioComponent from "@/app/components/RadioComponent";
import CheckComponent from "@/app/components/CheckComponent";
import SelectComponent from '@/app/components/SelectComponent';
import {Field, FieldArray ,useFormikContext} from 'formik';
//Data
import option_data from "@/app/json/data.json";
const '''+component_name+'''= ()=>{
const { isValid, isSubmitting,values,errors, touched, setFieldValue, setFieldTouched }:any = useFormikContext();
    return(
        <>
        <div className='grid grid-cols-1 gap-9 sm:grid-cols-2'>
          
          <div className='flex flex-col gap-9'>        
          '''+question_template+'''
          </div>
          <div className='flex flex-col gap-9'>
          </div>
        </div>        
        </>

    )
};
export default '''+component_name+''';
    '''

    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

    

def create_layout(title,dirname,gen_path,initialFormValues):
    filepath = os.path.join(os.path.sep,gen_path,'dashboard',dirname)
    filename = os.path.join(os.path.sep,filepath,'layout.tsx')    
    code = r'''"use client";
import { ReactNode, useEffect, useState } from 'react';
import {Formik, Form, yupToFormErrors, validateYupSchema, useFormikContext} from 'formik';
import { useRouter, usePathname } from "next/navigation";
import Header from '@/app/components/Header';
import Sidebar from '@/app/components/Sidebar';
import useAuth from '@/app/hooks/useAuth';

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
  const pathname = usePathname();
  const authCtx = useAuth();
  const userid = authCtx.userId;
  const mobileNumber = authCtx.activeMobileNumber;

  const [sidebarOpen, setSidebarOpen] = useState(false);

  let '''+title+''' ={
    '''+initialFormValues+'''
  };

  const fetch'''+title+'''Data = useCallback(async()=>{
    const response = await axios.get(`${url}get-'''+dirname+'''-question/${userid}/${mobileNumber}`);
    if(typeof window !== 'undefined' && response.data.data!=null){
      localStorage.setItem('data',JSON.stringify(response.data.data));
    }
  },[userid]);

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
    await axios.post(`${url}save-'''+dirname+'''-question`, 
    {
    userid:authCtx.userId,
    data:values,
    contactnumber:mobileNumber
    }, 
    {    
      headers: {
        'Content-Type': 'application/json'
      }
    }
    ) .then(function (response) {

      if(typeof window !== 'undefined' && response.data.contact_question_id){
        localStorage.removeItem('data');
      }
      router.push('/dashboard')

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
              <Formik 
              initialValues={'''+title+'''}
              validationSchema={'''+title+'''Schema} 
              onSubmit={handleFormSubmit}>              
                <Form >
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
    with open(filename, "w") as f:
        f.write(code)
    

def domload(cur, id):
    cur.execute('select *from question where questionnaire_id = %s',(id))
    data  = cur.fetchall()
    #print(os.getcwd())
    #print(STRUCUTRE_PATH)
    template_path = os.getcwd()+os.path.sep+STRUCUTRE_PATH

    initialFormValues = ''
    question_template = ''
    option_data = '{'
    validation_rules = r'''import { object, array, string, number, StringSchema } from "yup";
    export default object().shape({
    '''

    #for record in cur:
    for row in data:
        time.sleep(2)
        #print(record)
        print(row['label'])

        if(row['validation_rules']!=None and len(row['validation_rules']) > 2 ):
            rules = row['validation_rules'].replace("[this]",row['variable'])
            validation_rules+=''+row['variable']+':'+rules+',\n'

        if(row['type'] =='text' or row['type'] =='number'):
            template_path_text = os.path.join(os.path.sep, template_path,"text.html")
            text_template = open(template_path_text, 'r').read()
            text_template = text_template.replace("[variable]",row['variable'])
            #text_template = text_template.replace("[placeholder]",row['placeholder'])
            text_template = text_template.replace("[label]",row['label'])
            text_template = text_template.replace("[type]",row['type'])
            question_template+=text_template+"\n"
        if(row['type'] =='radio'):
            template_path_text = os.path.join(os.path.sep, template_path,"radio.html")
            text_template = open(template_path_text, 'r').read()
            text_template = text_template.replace("[variable]",row['variable'])
            text_template = text_template.replace("[label]",row['label'])
            question_template+=text_template+"\n"
        if(row['type'] =='checkbox'):
            template_path_text = os.path.join(os.path.sep, template_path,"checkbox.html")
            text_template = open(template_path_text, 'r').read()
            text_template = text_template.replace("[variable]",row['variable'])
            text_template = text_template.replace("[label]",row['label'])
            question_template+=text_template+"\n"

        if(row['type'] =='multiselect'):
            template_path_text = os.path.join(os.path.sep, template_path,"multiselect.html")
            text_template = open(template_path_text, 'r').read()
            text_template = text_template.replace("[variable]",row['variable'])
            text_template = text_template.replace("[label]",row['label'])
            question_template+=text_template+"\n"

        if(row['type'] =='dropdown'):
            template_path_text = os.path.join(os.path.sep, template_path,"dropdown.html")
            text_template = open(template_path_text, 'r').read()
            text_template = text_template.replace("[variable]",row['variable'])
            text_template = text_template.replace("[label]",row['label'])
            question_template+=text_template+"\n"
        list_options = {'radio','checkbox', 'multiselect', 'dropdown'}

        if(row['type'] in list_options):
            option_data+='"'+row['variable']+'":'+row['options']+',\n'
        ### inital variable generator
        if(row['type'] =='number'):
            initialFormValues+=row['variable']+':0,\n'
        if(row['type'] =='text' or row['type'] =='radio'):
            initialFormValues+=row['variable']+':"",\n'
        if(row['type'] =='dropdown'):
            initialFormValues+=row['variable']+':{value:\'\',label:\'\'},\n'    
        if(row['type'] =='checkbox' or row['type'] =='multiselect'):
            initialFormValues+=row['variable']+':[],\n'

    template_path_submit = os.path.join(os.path.sep, template_path,"submit.html")
    submit_template = open(template_path_submit, 'r').read()
    question_template+=submit_template+"\n"

    #create_layout(component_name, gen_path,initialFormValues)
    option_data += '}'
    validation_rules += r'''
    });
    '''
    pos_occurance = option_data.rfind(',')
    #pos_occurance_rules = validation_rules.rfind(',')
    option_data = option_data[:pos_occurance] + ' ' + option_data[pos_occurance+1:]
    #validation_rules = validation_rules[:pos_occurance_rules]+ ' '+validation_rules[pos_occurance_rules+1:]

    return (initialFormValues,question_template,option_data,validation_rules)

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


def create_option_data(gen_path,option_data):
  filepath = os.path.join(os.path.sep,gen_path,'json')
  filename = os.path.join(os.path.sep,filepath,'data.json')
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


if __name__ == '__main__':
    id = sys.argv[1]
    gen_path = sys.argv[2]
    conn = connect()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    component = create_component (cur,id,gen_path)
    component_name = component[0]
    component_file = component[1]
    title = component[2]
    domdata =  domload(cur, id)
    #print(domdata)
    init_form_values = domdata[0]
    question_template = domdata[1]
    option_data = domdata[2]
    validation_rules = domdata[3]
    
    create_questionarie(component_name,component_file,question_template)
    create_option_data(gen_path,option_data)
    create_validation_schema(gen_path, component_name, validation_rules)
    create_layout(component_name,title, gen_path, init_form_values)
    
    cur.close()
    conn.close()
