from fastapi import FastAPI, Form, Request, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import datetime
import humanize

import json

from sqlalchemy import create_engine
from sqlalchemy import desc
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, DateTime, Boolean, Interval
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URL = "sqlite:///fast.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
session = SessionLocal()

class Fast(Base):
    __tablename__ = 'fasts'
    id = Column(Integer, primary_key = True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    deleted = Column(Boolean)
    completed = Column(Boolean)
    duration = Column(Interval)
    planned_duration = Column(Integer)

    # classmethod to start new fast
    @classmethod
    def start_fast(cls, start, duration):
        if cls.active_fast():
            raise RuntimeError('Cannot create another active fast')
        else:
            fast = Fast(start_time = swap_dt(start), planned_duration = duration, deleted = False, completed = False)
            session.add(fast)
            session.commit()
            return fast

    @classmethod
    def get(cls, id):
        return session.query(cls).filter_by(id=id).first()

    @classmethod
    def active_fast(cls):
        return session.query(cls).filter(cls.deleted==False).filter(cls.completed==False).first()
    
    @classmethod
    def fast_history(cls):
        return session.query(cls).filter(cls.deleted==False).filter(cls.completed==True).order_by(desc(cls.start_time)).all()

    @classmethod
    def get_stats(cls):
        completed_fasts = cls.fast_history()
        

        fast_count = len(completed_fasts)
        if fast_count > 0:
            last_fast_time = max([x.end_time for x in completed_fasts])

            total_hours = sum([x.duration for x in completed_fasts],datetime.timedelta())
            total_hours_text = humanize.precisedelta(total_hours, minimum_unit="hours", format="%0.0f")

            longest_fast = max([x.duration for x in completed_fasts])
            longest_fast_text = humanize.precisedelta(longest_fast, minimum_unit="hours", format="%0.0f")

            now = datetime.datetime.today()
            time_passed = now - last_fast_time
            time_passed_text = humanize.precisedelta(time_passed, minimum_unit="hours", format="%0.0f")
            
            result_dict = {"fast_count": fast_count, "last_time_passed_text": time_passed_text,
                        "total_fasted_time": total_hours_text, "longest_fast_text": longest_fast_text,
                        "now": swap_dt(now)}
            return result_dict

    def delete_fast(self):
        self.deleted = True
        session.commit()
    
    #method for ending the fast
    def end_fast(self, time = None):
        self.completed = True
        if time:
            self.end_time = swap_dt(time)
        else:
            self.end_time = datetime.datetime.now()
        self.calculate_duration()
        session.commit()

    def calculate_duration(self):
        fast = self.get(self.id)
        if fast.completed:
            fast.duration = self.end_time - self.start_time
            session.commit()
            return fast.duration

    #method for editing the start and end date of a fast
    def edit_start(self, start):
        self.start = swap_dt(start)
        self.calculate_duration()
        session.commit()

    def edit_fast(self, start, duration):
        self.start_time = swap_dt(start)
        self.planned_duration = duration
        session.commit()

    def edit_end(self, end):
        self.end = swap_dt(end)
        self.calculate_duration()
        session.commit()

Base.metadata.create_all(engine)

def import_fast_data():
    with open ('data.json', 'r') as data_file:
        import_data = json.load(data_file)
        for fast in import_data:
            start_time = datetime.datetime.strptime(fast['Start'], '%Y-%m-%d %H:%M')
            end_time = datetime.datetime.strptime(fast['End'], '%Y-%m-%d %H:%M')
            x = Fast(start_time = start_time, end_time = end_time, completed = True, 
                     duration = end_time-start_time, deleted = False)
            session.add(x)
            session.commit()


def swap_dt(obje):
    if isinstance(obje, str):
        return datetime.datetime.strptime(obje, '%Y-%m-%dT%H:%M')
    elif isinstance(obje, datetime.datetime):
        return datetime.datetime.strftime(obje, '%Y-%m-%dT%H:%M')

def active_fast_info():
    graph_data = {}
    active_fast = Fast.active_fast()
    now = datetime.datetime.today()
    if active_fast:
        time_passed = now - active_fast.start_time
        time_passed_hour = time_passed.total_seconds() / (60 * 60)
        time_passed_text = humanize.precisedelta(time_passed, minimum_unit="hours", format="%0.0f")
        completion = ((time_passed.total_seconds() / (60 * 60)) / active_fast.planned_duration)*100
        
        start_date = active_fast.start_time.strftime('%a, %b %d')
        start_time = active_fast.start_time.strftime('%H:%M')
        start_time_data = swap_dt(active_fast.start_time)
        
        est_end_time = (active_fast.start_time + datetime.timedelta(hours = active_fast.planned_duration)).strftime('%H:%M')
        est_end_date = (active_fast.start_time + datetime.timedelta(hours = active_fast.planned_duration)).strftime('%a, %b %d')
        
        graph_data['score']= time_passed_hour
        graph_data['max'] = max(active_fast.planned_duration, time_passed_hour) + 1
        return {'fasting': True, "id": active_fast.id, 'time_passed_text': time_passed_text, 
                'completion': completion, 'start_date': start_date, 'start_time': start_time, 'est_end_time': est_end_time,
                'est_end_date': est_end_date, 'start_time_data': start_time_data, 'planned_duration': active_fast.planned_duration,
                'graph_data': graph_data}
    else:
        return {'fasting': False}


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/")

@app.get("/")
def start(request: Request, stats: dict = Depends(Fast.get_stats)):
    
    current_fast = active_fast_info()
    if current_fast:
        context={'request': request, 'current_fast':current_fast, "stats": stats}
        print(context)
        return templates.TemplateResponse('home.html', context=context)
    else:
        context={'request': request, "stats": stats}
        print(context)
        return templates.TemplateResponse('home.html', context=context)


@app.post("/StartFast/")
def startfast(request: Request, fdate = Form(...), fduration = Form(...)):
    new_fast = Fast.start_fast(fdate, fduration)
    response = RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)
    return response


@app.post("/EditFast/{id}")
def editfast(id, request: Request, fdate = Form(...), fduration = Form(...)):
    Fast.get(id).edit_fast(fdate, fduration)
    response = RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)
    return response



@app.get("/history/")
def showhistory(request: Request, stats: dict = Depends(Fast.get_stats)):
    current_fast = active_fast_info()

    fast_list = []
    for fast in Fast.fast_history():
        start_time = fast.start_time.strftime('%Y-%m-%d %H:%M')
        end_time = fast.end_time.strftime('%Y-%m-%d %H:%M')
        duration = humanize.precisedelta(fast.duration, minimum_unit="hours", format="%0.0f")
        fast_list.append({"id":fast.id, "start_time": start_time, "end_time":
        end_time, "duration":duration})

    context = {'request': request, 'fasts': fast_list, 'stats':stats, 'current_fast': current_fast}       
    return templates.TemplateResponse('history.html', context=context)


@app.get("/delete/{id}")
def delete_fast(id):
    Fast.get(id).delete_fast()
    response = RedirectResponse(url='/history')
    return response


@app.get("/api/end/{id}")
def end_fast_api(id, time):
    Fast.get(int(id)).end_fast(time)
    response = {'fast id': id, 'status': 'ended'}
    return response


@app.get("/end/{id}")
def end_fast(id, fdate):
    print(fdate)
    Fast.get(int(id)).end_fast(fdate)
    response = RedirectResponse(url='/')
    return response

#import_fast_data()