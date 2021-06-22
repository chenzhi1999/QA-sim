import numpy as np

'''
It processes the Bright star catalogue file to output
as an array [[star#1,RA1,DEC1,s1],[star#2,RA2,DEC2,s2]....]
'''


class BSC_process:
    def __init__(self, BSC_file):
        lis = []
        for line in open(BSC_file,"rt"):
            if (len(line[20:35].strip()) < 5 ):                     #Ignore stars that have no info
                continue
        
            star_num = int(line[0:4])
            try:
                RA_hours = float(line[75:77])          
                RA_min = float(line[77:79])
                RA_sec = float(line[79:83])
                RA = (RA_hours + RA_min/60 + RA_sec/3600)/24*360*np.pi/180    # RA for J2000
    
                DEC_sign = (line[83] == '-')
                DEC_deg = float(line[84:86])
                DEC_arcmin = float(line[86:88])
                DEC_arcsec = float(line[88:90])
                DEC = (DEC_deg + DEC_arcmin/60 + DEC_arcsec/3600)*np.pi/180   # DEC for J2000
    
                if DEC_sign:
                    DEC *= -1
                # lam ~ 0.55um, F_v,0 = 3640Jy
                V_mag = float(line[102:107])               # Convert to flux density
                s_V = 3640.*10**(V_mag/-2.5)                # flux density in Jy
                
            except ValueError:
                continue


            lis.append(star_num)
            lis.append(RA)
            lis.append(DEC)
            lis.append(s_V)
            
        self.pos_s = np.array(lis).reshape((len(lis)/4,4))    #[[star_num1,RA1,DEC1,s_V1],[star_num2,RA2,DEC2,s_V2],...]



    def BSC_filter(self,pos_t):
        # position of tele (pos_t) in [[RA1,DEC1,R1],[RA2,DEC2,R2]]

        pos_t = np.array(pos_t)

        
        #Select out stars that are never in the plane of tele, diff in DEC less than some deg
        cond1 = np.where((np.absolute(self.pos_s[:,2] - pos_t[0,1]) < np.pi/6.) &
                         (np.absolute(self.pos_s[:,2] - pos_t[1,1]) < np.pi/6.))

        pos_s = self.pos_s[cond1]

        #flux density condition: eliminate stars whose flux density is less than 50Jy
        cond2 = np.where(pos_s[:,3] > 50.0)
        pos_s = pos_s[cond2]
 
        #Create star pairs NxN matrix of all pairs and select out onces in the lower triangle:
        N = len(pos_s)
        row_del = []

        # might want better ways to do this. *Nested for-loop too time consuming.
        for i in range(N):
            for j in range(i+1):
                k = i*N+j
                row_del.append(k)

        pos_s_rep = np.tile(pos_s,(1,N)).reshape((N**2,4)) 
        pos_s_rep = np.delete(pos_s_rep, row_del, axis=0)  #[11111...22222....3333..]
        
        pos_s_seq = np.tile(pos_s,(N,1))
        pos_s_seq = np.delete(pos_s_seq, row_del, axis=0)  #[12345..23456..34567..]

        #[ [[num1,RA1,DEC1,S1],[num2,RA2,DEC2,S2]],.....]
        pos_s_mat = np.hstack((pos_s_seq,pos_s_rep)).reshape((N*(N-1)/2,2,4))

        # select out pairs of stars that are far away from each other
        # convert from spherical to carte? and find difference.

        def dis_diff(posi):
            # posi in (N,2,4) array and convert posi from RA,DEC to carte
            posi[:,:,2] = np.pi/2 - posi[:,:,2]        #DEC to THETA
            
            #change from spherical to cartesian
            x = np.sin(posi[:,:,2])*np.cos(posi[:,:,1])     #x,y,z for all pairs (N,2)
            y = np.sin(posi[:,:,2])*np.sin(posi[:,:,1])
            z = np.cos(posi[:,:,2])

            dx = np.absolute(x[:,1] - x[:,0])
            dy = np.absolute(y[:,1] - y[:,0])
            dz = np.absolute(z[:,1] - z[:,0])

            dis_diff = np.sqrt(dx*dx + dy*dy + dz*dz)      # 1-D N pair stars array
            
            return dis_diff
        
        dis_diff = dis_diff(pos_s_mat)
        cond3 = np.where(dis_diff < 0.01)     #dis_diff ~ angle in rad for small arc_length
        pos_s_mat = pos_s_mat[cond3]

        return pos_s_mat