Researchers created a new technique that accurately and rapidly matches X-rays captured during surgery with a patient’s preoperative 3D medical scan. This method could make it easier for clinicians to precisely pilot minimally invasive surgical tools, leading to faster and safer procedures.

Clinicians perform many minimally invasive surgeries using real-time X-rays to help them steer devices like catheters and endoscopes through tiny incisions. But since X-rays are flat images, it can be challenging to determine exactly where surgical tools are located and oriented within the patient’s body, increasing the risk of complications.

To help localize surgical devices, clinicians may manually align X-rays with preoperative 3D medical images, such as CT scans or MRIs. Artificial intelligence tools designed to streamline this process struggle to align images robustly for all patients, making them infeasible in practice.

This new system, developed by scientists and clinicians at MIT and collaborating institutions, uses an AI model that adapts to each patient in only about five minutes. The model automatically matches one patient’s X-rays with 3D scans in a matter of seconds, and with sub-millimeter precision.

Named xvr (which stands for X-ray volume registration), it outperformed existing AI methods by an order of magnitude across a wide range of patients, body parts, and medical procedures.

“A majority of Americans live more than an hour away from a center that can perform noninvasive procedures, like emergency stroke interventions. An hour in stroke time is incredibly substantial. Making these procedures easier by combining 2D and 3D information enables these types of highly specialized life-saving procedures to be more accessible to much broader parts of the population,” says Vivek Gopalakrishnan, a postdoc in the MIT Computer Science and Artificial Intelligence Laboratory (CSAIL); a recent graduate of the Harvard-MIT Program in Health Sciences and Technology; and lead author of a paper on xvr, which [appears today in *Nature*](https://www.nature.com/articles/s41586-026-11045-x).

He is joined on the paper by his advisor Polina Golland, the Sunlin and Priscilla Chou Professor of Electrical Engineering and Computer Science (EECS), a principal investigator in CSAIL, the leader of the Medical Vision Group, and co-senior author of the paper; and Neel Dey, a former postdoc in the Medical Vision Group who is now an investigator at Harvard Medical School and Massachusetts General Hospital as well as co-senior author on the paper. Additional co-authors include David-Dimitris Chlorogiannis, a researcher and clinician at Harvard Medical School; Andrew Abumoussa, a neurosurgeon at St. Luke’s Marion Bloch Neuroscience Institute; Anna M. Larson, a pediatric clinician at Shriners Children’s Hospital; Nazim Haouchine, an assistant professor of radiology at Harvard and Brigham and Women’s Hospital; Darren B. Orbach, a physician and scientist at Boston Children’s Hospital; and Sarah Frisken, an associate professor of radiology at Harvard.

**Making X-rays more informative**

In many minimally invasive surgical procedures, like angioplasty to open blocked arteries, clinicians insert instruments through a tiny incision and use a high-speed mobile X-ray scanner to generate images that allow them to visualize the procedure from any angle.

But to guide surgical tools without accidentally damaging other tissue, clinicians must align real-time X-rays with the patient’s preoperative MRI or CT scan. This process, called registration, helps them determine where the tool is in relation to anatomical structures.

“It takes decades of training for a clinician to become skilled enough to see grainy, 2D images and understand how everything is oriented. We want to make these 2D X-rays more informative, so it becomes safer and easier to do these life-saving procedures,” Gopalakrishnan says.

Manual registration methods are slow and burdensome, requiring the clinician to guess the position of a surgical instrument by punching numbers into a computer or clicking anatomical landmarks on a screen.

To streamline the process, researchers are developing AI models that can predict 2D/3D registration. But people have such diverse anatomy that a model which works well for some patients may fail for others.

A lack of high-quality annotated medical image data makes it difficult to train a deep-learning model robust enough to adapt to many patients, Gopalakrishnan says.

Rather than trying to make a machine-learning model that can be applied to all patients, the researchers built a model designed to adapt extremely well for the specific patient.

“We tailor this one specific model for this one specific patient, and it doesn’t matter if it works on other people because there will be different models for those people,” Gopalakrishnan adds.

**Patient-specific machine learning**

Xvr takes one patient’s preoperative 3D scan, like an MRI or CT, and uses it to generate thousands of synthetic X-rays from many angles, producing about 1,000 images each second. It uses a physics-based simulation of the X-ray process to ensure these synthetic images are realistic.

“Instead of generating data from nothing, like some types of generative AI, this physics simulation is entirely based on the CT scan or MRI from this patient. Because xvr creates patient-specific data in a purely physics-based manner, there is no room for hallucinations,” Gopalakrishnan says.

The xvr framework uses these simulated data to train an AI model that can accurately align this patient’s 2D X-rays with their 3D image scan in a matter of seconds.

But while such a registration model is highly accurate, it would take about 12 hours to train from scratch for each patient, making it impossible to deploy in an emergency. To make the process faster, the researchers used xvr to pretrain a more versatile AI system, called a foundation model, that can quickly adjust to each new patient.

They collected whole-body 3D medical scans from more than 2,000 patients covering a wide range of ages, image modalities, and regions. Xvr used these diverse data to generate synthetic X-rays and train a foundation model to perform 2D/3D registration.

This pretrained model can adapt to a new patient in about five minutes, and performs registration with the same accuracy as if it had been trained from scratch.

“So now you can get patient-specific accuracy but also in a very rapid time frame,” Gopalakrishnan says.

The team tested the model on the largest available dataset of real 2D/3D registrations, incorporating data from five hospitals that covered dozens of bones and organ systems in adult and pediatric patients.

Xvr significantly outperformed other AI-based methods in accuracy and robustness, while operating fast enough for emergency surgeries. The model could also be used to improve the performance of robotic surgery technologies.

In the future, the researchers hope to focus on making xvr faster for real-time deployment, conducting further studies to verify its reliability in additional situations, and extending the system to handle more complex scenarios, like moving body parts.

“For the past two years, we’ve been carefully developing this algorithm and validating it. Now, we are collaborating closely with surgical robotics companies and clinical groups to turn this research into useful tools for navigation or deployment,” Gopalakrishnan says.

This work was funded, in part, but the National Institutes of Health (NIH), the MIT CSAIL-Wistron Program, the MIT-IBM Computing Research Lab, the MIT Jameel Clinic, the MIT Health and Life Sciences Collaborative, and the Chou Family Transformative Research Fund.