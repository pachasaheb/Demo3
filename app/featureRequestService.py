from app import FeatureRequestApp
# from sqlalchemy we can import ascending order
from sqlalchemy import asc
# imports all exceptetions from sqlalchemy package
from sqlalchemy.exc import *
import psycopg2
# from config.py imports Config class for importing Session
from config import Config

# FeatureRequestService class is used to create Feature Request by using createFeatureRequestService function
# FeatureRequestService class is used to retrieve  Feature Request Details by using retrieveFeatureRequestService function
# FeatureRequestService class is used to edit  Feature Request Details by using editFeatureRequestService function
class FeatureRequestService:
    """FeatureRequestService Class is used to create, retrieve and edit Feature Requests into/from Postgresql database"""
    # __init__ is default constructor used to declare a class level session variable which can be set or get whenever required for a session
    def __init__(self):
        self.session= ''

    # setSession function is used to set session variable for example to set mock sessions
    def setSession(self, argSession):
        self.session= argSession

    # getSession function is used to get session which is used to create and retrieve values
    def getSession(self):
        if self.session == '':
            print("Inside IF")
            self.session= Config.Session()
            return self.session
            
        else:
            print("Inside Else")
            return self.session
    
    # createFeatureRequestService function accepts FeatureRequestApp model class instance which and persits all the values into database
    def createFeatureRequestService(self,featureRequestApp):
        try:
            print("Inside Create Feature Request Service")
            # dbsession variable gets session from class function getSession()
            dbsession=self.getSession()
            # Checking if any rows available in database or not
            if len(dbsession.query(FeatureRequestApp).all()) > 0 :
                # For Reprioritizing client priority
                self.reprioritizeFeatureRequestService(featureRequestApp)
            else:
                # Else FeatureRequests for a particular client are empty then this FeatureRequest is considered and First Priority and is added to the particular client
                dbsession.add(FeatureRequestApp(featureRequestApp.title, featureRequestApp.description, featureRequestApp.client,1,featureRequestApp.targetDate,featureRequestApp.productArea))
                dbsession.commit()
            # Returns a String Response
            return 'success'
            
        except IntegrityError as ie:
            dbsession.rollback()
            print("Title name already exists.Please change name.",ie)
            return 'Title name already exists.Please change name.'

        except psycopg2.IntegrityError as pie:
            dbsession.rollback()
            print("Title name already exists.Please change name.",pie)
            print("Inside pie")
            return 'Title name already exists.Please change name.'

        except Exception as e:
            dbsession.rollback()
            print("Error Occured in createFeatureRequestService",e)
            return 'Error Occured'

        finally:
            dbsession.close_all() 
       
    # retrieveFeatureRequestService funcition is used to retrieve all the details of FeatureRequests and assigns it to array output  
    def retrieveFeatureRequestService(self):
        try:
            # dbsession variable gets session from class function getSession()
            dbsession=self.getSession()
            print("inside retrieve Feature Request Service")
            # Stores the database objects into details according to the query should retrieve all records present in database according to ascending order of client priority and client
            details=dbsession.query(FeatureRequestApp).order_by(asc(FeatureRequestApp.client),asc(FeatureRequestApp.clientPriority)).all()
            # declaring an empty array
            output = []
            # Iterating the deatails so each and every record are seperated and assigned to detail_data tuple and in last each and every data tuple to output array
            for detail in details:
                detail_data ={}
                detail_data['featureId']=detail.featureId
                detail_data['title']=detail.title
                detail_data['description']=detail.description
                detail_data['client']=detail.client
                detail_data['clientPriority']=detail.clientPriority
                detail_data['targetDate']=detail.targetDate
                detail_data['productArea']=detail.productArea
                output.append(detail_data)
            # returns output array with all the records retrieved from database
            return output

        except Exception as e:
            dbsession.rollback()
            print("Error Occured in retrieveFeatureRequestService",e)
            return 'Error Occured'

        finally:
            dbsession.close_all() 

    # reprioritizeFeatureRequestService function is used to retrieve the Request Details from Database
    def reprioritizeFeatureRequestService(self,featureRequestApp):
        print("Inside reprioritize Feature Request Service")
        # dbsession variable gets session from class function getSession()
        dbsession= self.getSession()
        updateStart= int(featureRequestApp.clientPriority)
        updateClient= featureRequestApp.client
        # Filter total rows according to given Client name
        totalRows=len(dbsession.query(FeatureRequestApp).filter_by(client = updateClient).all())
        # Checking whether given client priority less than or equal to total rows
        if updateStart <= totalRows:
            # Running for loop according to client Priority
            for updateStart in range(updateStart, totalRows+1, 1):
                updateRow = dbsession.query(FeatureRequestApp).filter_by(clientPriority=updateStart, client = updateClient).first()
                updateRow.clientPriority = updateStart+1

            dbsession.add(featureRequestApp)
            dbsession.commit()
        # if given priority is greater than total number of rows then update as total+1 in client priority
        else:
            dbsession.add(FeatureRequestApp(featureRequestApp.title, featureRequestApp.description, featureRequestApp.client, totalRows+1,featureRequestApp.targetDate,featureRequestApp.productArea))
            dbsession.commit()

    
    # editFeatureRequestService function is used to retrieve the Request Details from Database
    def editFeatureRequestService(self,featureRequestApp):
        try:
            print("Inside editFeatureRequestService") 
            # dbsession variable gets session from class function getSession() 
            dbsession= self.getSession()
            # Taking client priority from where the list degrade meaning reordering the rows present below the updated request
            degradeStart=(dbsession.query(FeatureRequestApp).filter_by(title=featureRequestApp.title).first()).clientPriority
            # Deleting the past request according to the title name of present updated request inorder to avoid repeatition of client priority
            dbsession.delete(dbsession.query(FeatureRequestApp).filter_by(title=featureRequestApp.title).first())
            # Reordering the client priority of rows present below the past record of present updated request
            for degradeStart in range(degradeStart,len(dbsession.query(FeatureRequestApp).filter_by(client = featureRequestApp.client).all())+1,1):
                updateRow = dbsession.query(FeatureRequestApp).filter_by(clientPriority=degradeStart+1, client = featureRequestApp.client).first()
                updateRow.clientPriority = degradeStart
            dbsession.commit()
            # Passing present updated record to reprioritizeFeatureRequestService to reorder the remaining rows
            self.reprioritizeFeatureRequestService(featureRequestApp)
            # Returns a String Response
            return 'success'

        except Exception as e:
            dbsession.rollback()
            print("Error Occured in createFeatureRequestService",e)
            return 'Error Occured'

        finally:
            dbsession.close_all() 
            
     