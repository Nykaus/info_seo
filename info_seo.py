import urllib.request
import re
import webbrowser
import os
import sublime, sublime_plugin
import json


#ctrl+alt+w  selection un url
class OpenWebCommand(sublime_plugin.TextCommand):
	def run(self,edit):
		#recuperation des selections faites sur l'editeur
		tabRegion=self.view.sel()
		for laRegion in tabRegion:
			checkUrl="http://"+self.view.substr(laRegion).replace("http://","").replace("https://","")
			webbrowser.open(checkUrl)

#ctrl+alt+m selection un url
class GetRefCommand(sublime_plugin.TextCommand):
	def run(self,edit):
		#recuperation des selections faites sur l'editeur
		tabRegion=self.view.sel()
		cpt=0
		for laRegion in tabRegion:
			lUrl=self.view.substr(laRegion)
			lUrl = re.sub(r"http[s]?:\/\/","",lUrl)
			checkUrl="http://"+lUrl

			# ouverture de la page selectionner
			statusError=0
			try:				
				sock = urllib.request.urlopen(checkUrl)
				htmlSource = sock.read().decode("utf-8", 'ignore')
				sock.close()	
			except Exception as e:
				statusError=1
				msgErreur = "\n\n================ERREUR====================\n\t"
				msgErreur += str(e)+"\n\t"+self.view.substr(laRegion)
				msgErreur += "\n==========================================\n\n"
				self.view.replace(edit, laRegion,msgErreur)

			if(statusError==0):
				data=None
				# recuperation les parametres de trie des urls
				pathSettings=__file__.replace("info_seo.py", "info_seo_settings.json")	
				json_data=open(pathSettings)
				data = json.load(json_data)
				json_data.close()
				
				if data != None:
					getref_isvisible = data["GetRef"]["visible"]
					if htmlSource=="":			
						self.view.replace(edit, laRegion,"ERREUR !! Auncun contenu pour URL: '"+checkUrl+"'")
					else:

						txtResultat="====================================\n"
						txtResultat+=checkUrl+"\n"
						txtResultat+="====================================\n"
						
						if getref_isvisible["title"]: 
							txtResultat+="------Title------\n\n"
							arrTitle = re.findall(r'<title.*>(.*)</title>', htmlSource)
							for Title in arrTitle:
								txtResultat+="\t"+Title+"\n"

						if getref_isvisible["description"]: 
							txtResultat+="\n------meta Description------\n\n"
							arrMeta = re.findall(r'<meta[^\"]*name="description"[^\"]*content="([^\"]*)"[^\>]*\/>', htmlSource)
							for Meta in arrMeta:				
								txtResultat+="\t"+Meta+"\n"

						if getref_isvisible["canonical"]: 
							txtResultat+="\n------Canonical------\n\n"		
							arrCanonical = re.findall(r'<link[^\"]*rel="canonical"[^\"]*href="([^\"]*)"[^\"]*>', htmlSource)				
							for Canonical in arrCanonical:
								txtResultat+="\t"+Canonical+"\n"
				
						if getref_isvisible["hn"]["format"]["in_line"] or getref_isvisible["hn"]["format"]["with_content"]: 
							txtResultat+="\n------HN------\n\n"			
							arrHN = re.findall(r'<h([1-5])(.*?)>(.*?)<\/h[1-5]>', htmlSource.replace("\n","").replace("\r",""))
							
							if getref_isvisible["hn"]["format"]["in_line"]:
								txtHN=""
								for HN in arrHN:
									txtHN+="\tH"+HN[0]+" - "

								txtResultat+= txtHN.strip(' - ')+"\n\n"

							if getref_isvisible["hn"]["format"]["with_content"]:
								for HN in arrHN:
									for nbTab in range(0,int(HN[0])):
										if nbTab > 0:
											txtResultat+="\t"
									txtResultat+="\tH"+HN[0]+" : "+HN[2]+"\n\n"
							

						self.view.replace(edit, laRegion, txtResultat)

#ctrl+alt+l selection un url
class GetUrlCommand(sublime_plugin.TextCommand):
	def run(self,edit):

		#recuperation des selections faites sur l'editeur
		tabRegion=self.view.sel()

		for laRegion in tabRegion:
			lUrl=re.sub("http[s]?://","",self.view.substr(laRegion))			

			if "/" in lUrl:
				Url=lUrl.split("/",2)
				nomDomaine=Url[0].replace("/","")
				Uri=Url[1]
			else:
				nomDomaine=lUrl
				Uri=""
				
			checkUrl="http://"+lUrl
			statusError=0

			# ouverture de la page selectionner
			try:				
				sock = urllib.request.urlopen(checkUrl)
				htmlSource = sock.read().decode("utf-8", 'ignore')
				sock.close()	
			except Exception as e:
				statusError=1
				msgErreur ="\n\n================ERREUR====================\n\t"
				msgErreur +=str(e)+"\n\t"+self.view.substr(laRegion)
				msgErreur +="\n==========================================\n\n"
				self.view.replace(edit, laRegion,msgErreur)
            
            # recuperation des informations est passé sans erreur
			if(statusError==0):
				# verifier si le contenu du site est récupéré
				if(htmlSource==""):		
					self.view.replace(edit, laRegion,"ERREUR !! Auncun contenu pour URL: '"+checkUrl+"'")
				else:
					txtResultat="====================================\n"
					txtResultat+=checkUrl+"\n"
					txtResultat+="====================================\n\n"

					# recuperation les parametres de trie des urls
					data = None
					pathSettings=__file__.replace("info_seo.py", "info_seo_settings.json")	
					json_data=open(pathSettings)
					data = json.load(json_data)
					json_data.close()

					if(data != None):
						exception_patterns   = data["GetUrl"]['domain']['exception']
						delete_info_patterns = data["GetUrl"]["url"]["delete"]
						clean_info_patterns  = data["GetUrl"]["url"]["clean"]

						# trie des informations récupéré
						links = re.findall(r'href=[\'"]?([^\'">]+)', htmlSource)
						
						arrLinks=[]			
						for link in links:
							
							#supprimer la recherche en fonction d'un pattern dans le fichier settings
							if (delete_info_patterns is not [] or delete_info_patterns is not None):
								rep_DI = 0
								countValid = 0
								for DI_pattern in delete_info_patterns:
									if re.search(r""+DI_pattern+"", link):
										countValid+=1
								if countValid > 0:
									continue


							# initialiser si le domaine doit etre visible généralement
							domain_isvisible     = data["GetUrl"]["domain"]['visible']
							# recuperer si me nom de domaine doit etre visible sur les urls
							if domain_isvisible and (exception_patterns is not [] or exception_patterns is not None):
								# enlever le nom domaine au url en fonction des patterns
								countValid = 0
								for E_pattern in exception_patterns:
									if re.search(r""+E_pattern+"",link):
										countValid+=1
								# si il y a plusieurs pattern qui ne valide pas ce lien il refuse d'ajoute le nom de domaine
								if countValid > 0:
									domain_isvisible=0

							# nettoyage dans url
							if (clean_info_patterns is not [] or clean_info_patterns is not None):
								for CI_pattern in clean_info_patterns:
									link = re.sub(r""+CI_pattern+"", "",link)

							# condition pour ajouter le nom de domaine devant l'url
							if domain_isvisible:
								arrLinks +=["http://"+nomDomaine+link]
							else:
								arrLinks +=[link]

						# trier les urls		
						arrLinks.sort()
						# supprimer les doublons et trier		
						tmpLines=['none']
						for line in arrLinks:
							unique = 1
							for tmpLine in tmpLines:
								if tmpLine == line:
									unique = 0
							if unique:
								tmpLines += [line] 
								txtResultat+=line+"\n"
						
						self.view.replace(edit, laRegion,txtResultat)

#ctrl+alt+g selection un url
class GetGoogleCommand(sublime_plugin.TextCommand):
	def run(self,edit):
		tabRegion=self.view.sel()
		for laRegion in tabRegion:
			laRecherche=self.view.substr(laRegion).replace(" ","+")
			checkUrl="https://www.google.fr/search?q="+laRecherche
			webbrowser.open(checkUrl)
