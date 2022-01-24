import sys,os
sys.path=[" /home/Zhi/april/py"]+sys.path
from Parameter import Parameter
from BaseLikelihood import BaseLikelihood
import numpy as np



class sim_like(BaseLikelihood):
    
    def __init__(self, seed, pos_t, pos_s, t, lam):  # seed = [V_init,d_ra_init, d_dec_init]
        BaseLikelihood.__init__(self,"sim_data")  
        
        # free par
        self.seed = seed
        self.V = seed[0]
        self.d_ew = seed[1]
        self.d_ns = seed[2]
        self.offset = seed[3]
        
        # fixed values
        self.t = t             # timestamp for the sim data
        
        self.baseline = np.array(pos_t)
        
        pos_s = np.delete(pos_s, 0, axis=1)  # delete star # part.
        self.pos_s = pos_s     # position of sources to determine midpoint
        
        self.lam = lam         # lambda for observation
        self.Omega_E = 7.292e-5
       
    def freeParameters(self):
        return [
                Parameter("V", self.seed[0], err=0.04,bounds=(0.0,1.0)),    #0.1 for 1arcsec ,bounds=(-0.1,0.7)
                Parameter("d_ew",self.seed[1], err=3e-10),   #5e-10
                Parameter("d_ns",self.seed[2], err=5e-10),
                Parameter("offset",self.seed[3], err=np.pi/10,bounds=(-np.pi/2,np.pi/2))   #bounds=(-np.pi,np.pi)
                ]
    
    def updateParams(self,params):    #params is also a class, updates param value.
        for p in params:
            if p.name=="V":
                self.V=p.value
            if p.name=="d_ew":
                self.d_ew=p.value
            if p.name=="d_ns":
                self.d_ns=p.value
            if p.name=="offset":
                self.offset=p.value
                
        
    def source_pos(self,ti):
        N = ti.size
        M = len(self.pos_s)  
            
        PHI = self.pos_s[:,0]
        PHI_mid = np.tile((PHI[0]+PHI[1])/2,(N))-self.Omega_E*ti
        DEC = self.pos_s[:,1]
        DEC_mid = np.tile((DEC[0]+DEC[1])/2,(N))  
            
        dx = -np.sin(DEC_mid)*np.cos(PHI_mid)*self.d_ns-self.d_ew*np.sin(PHI_mid)
        dy = -np.sin(DEC_mid)*np.sin(PHI_mid)*self.d_ns+self.d_ew*np.cos(PHI_mid)
        dz = self.d_ns*np.cos(DEC_mid)
           
        new_posi = np.column_stack((dx,dy,dz))
        
        return new_posi

    
    
    def get_phase(self):      
        new_pos_s = self.source_pos(self.t)
        
        dot = -self.baseline[1]*np.sin(self.baseline[2])*new_pos_s[:,0] + self.baseline[0]*new_pos_s[:,1] \
              +self.baseline[1]*np.cos(self.baseline[2])*new_pos_s[:,2]
       
        phase = 2*np.pi/self.lam*dot + self.offset   # Total phase with the offset
        
        return phase
    
    
    def loglike_wprior(self):
        
        phase = self.get_phase()
        loglike = np.log(1+self.V*np.cos(phase))  #get loglike for diff phase in 2d array[[],[],[
        
        res = np.sum(loglike, axis=None)
        #print(self.baseline[0])
        return res