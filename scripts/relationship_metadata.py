import pandas as pd

class RelationshipMetadata():

      def __init__(self,metadata,initialize=False):

          if not initialize:  
              self.rm = pd.read_pickle('relationship_metadata')          
          else:
              data = {'Variable1' : [],'Variable2' : [], 'Var1' : [],'Var2' : [], 'IgnoreList' :  [],'BlackList' : []}
              self.rm = pd.DataFrame(data)
              self.rm = self.rm.set_index(['Variable1','Variable2']).sort_index()

          # create all relationships
          a = []
          b = []  
          bl = []
          for n in metadata.index:
              for m in metadata.index:
                  if (n,m) not in self.rm.index:
                    a.append(n)
                    b.append(m)
                    # add two relationships that are both interventions on black list
                    if metadata['Intervention'].loc[n] != 'Intervention' or metadata['Intervention'].loc[m] != 'Intervention': 
                       bl.append(False)
                    else:
                       bl.append(True)
          
          newdata = {'Variable1' : a, 'Variable2' : b, 'Var1' : a,'Var2' : b, 'IgnoreList' :  [False for b in bl],'BlackList' : bl}
          newdf = pd.DataFrame(newdata).set_index(['Variable1','Variable2']).sort_index()
          self.rm = pd.concat([self.rm,newdf])
          self.save()


      def add_on_ignore_list(self,name1,name2):
          self.rm.loc[(name1,name2),'IgnoreList']=True
          self.rm.loc[(name2,name1),'IgnoreList']=True
          self.save()

      def add_on_black_list(self,name1,name2):
          self.rm.loc[(name1,name2),'BlackList']=True
          self.rm.loc[(name2,name1),'BlackList']=True
          self.save()

      def remove_from_ignorelist(self,name1,name2):
          self.rm.loc[(name1,name2),'IgnoreList']=False
          self.rm.loc[(name2,name1),'IgnoreList']=False
          self.save()

      def remove_from_blacklist(self,name1,name2):
          self.rm.loc[(name1,name2),'BlackList']=False
          self.rm.loc[(name2,name1),'BlackList']=False
          self.save()

      def is_on_ignore_list(self,pairs):
          return self.rm.loc[pairs,'IgnoreList'].to_list()

      def is_on_black_list(self,pairs):
          return self.rm.loc[pairs,'BlackList'].to_list()

      def save(self):
          self.rm.to_pickle('relationship_metadata')

          
          
