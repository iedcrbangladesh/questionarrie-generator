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


def create_questionarie(component_name, filename, question_template,title,demograph_data):

    demograph_data_template = ''
    if len(demograph_data)>0:
      print(demograph_data)
      for row in demograph_data:
        demograph_data_template+='import '+row+'_data from "@/app/json/'+row+'.json";\n'



    component_name = re.sub('[^A-Za-z]+', '', component_name).capitalize()
    code = r'''"use client";
//Library
import Link from "next/link";
import RadioComponent from "@/app/components/RadioComponent";
import CheckComponent from "@/app/components/CheckComponent";
import SelectComponent from '@/app/components/SelectComponent';
import SelectNonCreatableComponent from '@/app/components/SelectNonCreatableComponent';
import useAuth from '@/app/hooks/useAuth';
import { useRouter } from "next/navigation";


import {Field, FieldArray ,useFormikContext} from 'formik';
import {useEffect} from 'react';

//Data
import option_data from "@/app/json/'''+title+'''_data.json";
'''+demograph_data_template+'''
//Logical On Off
import { disable_logic, skip_logic } from "@/app/api/logic-checker";

const '''+component_name+''' = ()=>{

const router = useRouter();
const authCtx = useAuth();
const focus_element:any = authCtx.focusElement;
const redirect:any = authCtx.redirect;

useEffect(()=>{
  if(redirect!=null && redirect!=""){
    router.push(redirect)    
    authCtx.redirect = null;
    authCtx.setRedirect(null);
  }    
},[redirect,router,authCtx])

useEffect(()=>{

    if(focus_element!=null && focus_element!="" && typeof window!='undefined'){
      const fel = '#'+focus_element.replace('.','_');
      const scrollElement:any = document.querySelector(fel);
      console.log(scrollElement)
      if(scrollElement!=null){
        scrollElement.scrollIntoView({ behavior: "smooth" })
        authCtx.focusElement = null;
        authCtx.setFocusElement(null);
      }
      
    }

},[focus_element, authCtx])

const redirect_or_focus_location = (v:any, name:any, rule:any)=>{
  if(v!=null){
    const redirect_element = skip_logic(name,v.value,rule);
    if(redirect_element.redirect!=null){
      authCtx.setRedirect(redirect_element.redirect)   
    }    
    if(redirect_element.focusElement!=null){
      authCtx.setFocusElement(redirect_element.focusElement)
    }
  }
}
  



const { isValid, isSubmitting,values,errors, touched, setFieldValue, setFieldTouched }:any = useFormikContext();
    return(
        <>
        <div className='grid grid-cols-1 gap-9 sm:grid-cols-1'>
          
          <div className='flex flex-col gap-9'>        
          '''+question_template+'''
          </div>
          
        </div>        
        </>

    )
};
export default '''+component_name+''';
    '''

    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

    

def create_section(slug,gen_path,title):
    section_path = os.path.join(os.path.sep,gen_path,'dashboard',title,slug)
    section_file = os.path.join(os.path.sep,section_path,'page.tsx')
    if not os.path.exists(section_path):
      try:
        os.mkdir(section_path) 
      except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
          raise
    
    return section_file

def disable_logic_generator(rules):
  rules = json.loads(rules)
  rule_template = '['
  for rl in rules:
    res = list(rl.keys())[0]
    #print(res)
    rule_template+='"'+res+'",'

  pos_occurance = rule_template.rfind(',')
  rule_template = rule_template[:pos_occurance] + ' ' + rule_template[pos_occurance+1:]

  rule_template+=']'

  rule_template='disable_logic(name,v.value, setFieldValue,'+ rule_template+');'

  return rule_template

def skip_logic_generator(rules):
  rules = json.loads(rules)
  keys = list(rules.keys())
  #print(len(keys))
  rule_template = ''
  if(len(keys) > 1):
    for k in keys:
      rule_template+='\n redirect_or_focus_location(v,name,"'+ k+'"); \n'    
  else:
    rule_template='\n redirect_or_focus_location(v,name,"'+ keys[0]+'"); \n'

  #rule_template = list(rules.keys())[0]
  #print(list(rules.keys()))  
  #rule_template='\n redirect_or_focus_location(v,name,"'+ rule_template+'"); \n'
  

  return rule_template 

def do_all_segment(row,text_template,slug):

    text_template = text_template.replace("[sl]",row['question_label'])
    text_template = text_template.replace("[variable]",f"{slug}.{row['variable']}")
    text_template = text_template.replace("[error_slug]",f"{slug}")
    text_template = text_template.replace("[error_variable]",f"{slug}.{row['variable']}")
    text_template = text_template.replace("[id]",f"{slug}_{row['variable']}")
    
    label = row['label'].replace("\n","<br/>")
    text_template = text_template.replace("[label]",label)

    #text_template = text_template.replace("\n","<br/>")
    text_template = text_template.replace("[error_label]",row['error_label'])


    #instruction
    if(row['instruction'] is not None):
      instruction = row['instruction'].replace("\n","<br/>")              
      text_template = text_template.replace("[instruction]",instruction)      
    else:
      text_template = text_template.replace("[instruction]","") 

    #disabled_logic
    #print(row['disabled_rules'] is not None)
    
    if(row['disabled_rules'] is not None):
      #print(type(row['disabled_rules']))
      disabled_rules = disable_logic_generator(row['disabled_rules'])
      
      text_template = text_template.replace("[disable_logic]",disabled_rules)
      #print(row['disabled_rules'])
    else:
      text_template = text_template.replace("[disable_logic]","")
    
    #end disabled_logic

    #skip logic
    if(row['skip_logic'] is not None):
      skip_rules = skip_logic_generator(row['skip_logic'])
      #print(skip_rules)
      text_template = text_template.replace("[skip_logic]",skip_rules)
      #print(row['skip_logic'])
    else:
      text_template = text_template.replace("[skip_logic]","")
    #end skip logic

    #enabled rules
    #print(type(row['enabled_rules']))
    if(row['enabled_rules'] is not None):
      text_template = text_template.replace("[enabled_rules]","{"+row['enabled_rules'])
      text_template = text_template.replace("[_enabled_rules]",")}")
    else:
      text_template = text_template.replace("[enabled_rules]","")
      text_template = text_template.replace("[_enabled_rules]","")

    #end enabled rules

    #custom attributes
    if(row['custom_attributes']!=None):
      custom_attributes = json.loads(row['custom_attributes'])
      for c_a in custom_attributes:
        if(c_a['label']=='man_label'):
           text_template = text_template.replace("[man]",c_a['value'])                                              
        if(c_a['label']=='women_label'):
           text_template = text_template.replace("[women]",c_a['value'])          



    #end custom attributes

    return text_template


def question_section_wise(cur, id,gen_path, title):
    #cur.execute('select *from question where questionnaire_id = %s',(id))
    #data  = cur.fetchall()
    cur.execute('select *from section where questionnaire_id = %s order by section_order asc',(id))
    sections  = cur.fetchall()
    

    template_path = os.getcwd()+os.path.sep+STRUCUTRE_PATH
    
    index = 1
    for section in sections:
      slug = section['slug']
      type_section = section['type']
      question_template = ''
      section_id = int(section['id'])
      #print(section_id)
      demograph_data = []
      cur.execute('select *from question where section_id = %s order by question_order asc',(section_id,))
      questions = cur.fetchall()
      if(questions):
        section_path = create_section(str(index)+slug,gen_path,title)
        for row in questions:
           
            if(row['type'] in {'text','number'}):
              template_path_text = os.path.join(os.path.sep, template_path,"text.html")
              text_template = open(template_path_text, 'r').read()
              text_template = do_all_segment(row,text_template,slug)              
              text_template = text_template.replace("[type]",row['type'])
              question_template+=text_template+"\n"

            if(row['type'] =='radio'):
              template_path_text = os.path.join(os.path.sep, template_path,"radio.html")              
              text_template = open(template_path_text, 'r').read()
              text_template = do_all_segment(row,text_template,slug)                                      
              question_template+=text_template+"\n"
              

            if(row['type'] =='checkbox'):
              template_path_text = os.path.join(os.path.sep, template_path,"checkbox.html")
              text_template = open(template_path_text, 'r').read()
              text_template = do_all_segment(row,text_template,slug)
              question_template+=text_template+"\n"

            if(row['type'] =='multiselect'):
              template_path_text = os.path.join(os.path.sep, template_path,"multiselect.html")
              text_template = open(template_path_text, 'r').read()
              text_template = do_all_segment(row,text_template,slug)
              question_template+=text_template+"\n"

            if(row['type'] =='dropdown'):
              template_path_text = os.path.join(os.path.sep, template_path,"dropdown.html")
              text_template = open(template_path_text, 'r').read()
              text_template = do_all_segment(row,text_template,slug)              
              question_template+=text_template+"\n"
            
            if(row['type'] =='age_dropdown'):
              template_path_text = os.path.join(os.path.sep, template_path,"dropdown-noncreatable.html")
              text_template = open(template_path_text, 'r').read()
              text_template = do_all_segment(row,text_template,slug)
              question_template+=text_template+"\n"

            if(row['type'] =='text_radio'):
              template_path_text = os.path.join(os.path.sep, template_path,"text-radio.html")
              text_template = open(template_path_text, 'r').read()
              text_template = do_all_segment(row,text_template,slug)
              question_template+=text_template+"\n"

            if(row['type'] =='hour_minutes'):
              template_path_text = os.path.join(os.path.sep, template_path,"hour-minute.html")
              text_template = open(template_path_text, 'r').read()
              text_template = do_all_segment(row,text_template,slug)
              question_template+=text_template+"\n"

            if(row['type'] =='man_women_count'):
              template_path_text = os.path.join(os.path.sep, template_path,"man-women-count.html")
              text_template = open(template_path_text, 'r').read()
              text_template = do_all_segment(row,text_template,slug)
              question_template+=text_template+"\n"

            #demographics data  
            if(row['type'] == 'district_dropdown'):
                demograph_data.append(row['type'].replace("_dropdown",""))
                template_path_text = os.path.join(os.path.sep, template_path,"dropdown-dq-non.html")
                text_template = open(template_path_text, 'r').read()
                text_template = text_template.replace("[data]",row['type'].replace("_dropdown","_data"))
                text_template = do_all_segment(row,text_template,slug)
                question_template+=text_template+"\n"

            if(row['type'] == 'citycorporation_dropdown'):
                demograph_data.append(row['type'].replace("_dropdown",""))
                template_path_text = os.path.join(os.path.sep, template_path,"dropdown-dq-non.html")
                text_template = open(template_path_text, 'r').read()
                text_template = text_template.replace("[data]",row['type'].replace("_dropdown","_data"))
                text_template = do_all_segment(row,text_template,slug)
                question_template+=text_template+"\n"

            if(row['type'] == 'municipality_dropdown'):
                demograph_data.append(row['type'].replace("_dropdown",""))
                template_path_text = os.path.join(os.path.sep, template_path,"dropdown-dg.html")
                text_template = open(template_path_text, 'r').read()
                text_template = text_template.replace("[data]",row['type'].replace("_dropdown","_data"))
                text_template = do_all_segment(row,text_template,slug)
                question_template+=text_template+"\n"

            if(row['type'] == 'upazilla_dropdown'):
                demograph_data.append(row['type'].replace("_dropdown",""))
                template_path_text = os.path.join(os.path.sep, template_path,"dropdown-dg.html")
                text_template = open(template_path_text, 'r').read()
                text_template = text_template.replace("[data]",row['type'].replace("_dropdown","_data"))
                text_template = do_all_segment(row,text_template,slug)
                question_template+=text_template+"\n"

            

        #template_path_text = os.path.join(os.path.sep, template_path,"debug.html")
        #text_template = open(template_path_text, 'r').read()
        #question_template+=text_template+"\n"

        create_questionarie(section['slug'],section_path,question_template,title, demograph_data)
        print(row['label'])
        index+=1
        time.sleep(1)  
      
      if(type_section > 0):
        section_path = create_section(str(index)+slug,gen_path,title)
        template_path_text = os.path.join(os.path.sep, template_path,"submit.html")
        text_template = open(template_path_text, 'r').read()
        text_template = text_template.replace("[section_instruction]",section['instruction'])
        #question_template+=text_template+"\n"
        #print(question_template)
        create_questionarie(section['slug'],section_path,text_template,title,[])
        index+=1
        #time.sleep(1)
      
                   


    
    
    
    

    
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




if __name__ == '__main__':
    id = sys.argv[1]
    gen_path = sys.argv[2]
    conn = connect()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    component = create_component (cur,id,gen_path)
    component_name = component[0]
    component_file = component[1]
    title = component[2]
    question_section_wise(cur,id,gen_path,title)
    
    
    
    cur.close()
    conn.close()
