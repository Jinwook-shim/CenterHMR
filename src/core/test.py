from base import *

class Demo(Base):
    def __init__(self):
        super(Demo, self).__init__()
        self.set_up_smplx()
        self._build_model()
        self.save_mesh = args.save_mesh
        self.save_centermap = args.save_centermap
        self.save_dict_results = args.save_dict_results
        self.demo_dir = os.path.join(config.project_dir, 'demo')
        print('Initialization finished!')

    def run(self, image_folder):
        vis_size = [1024,1024,3]#[1920,1080]
        self.generator.eval()
        loader_val = self._create_single_data_loader(dataset='internet',train_flag=False, image_folder=image_folder)
        test_save_dir = image_folder+'_results'
        os.makedirs(test_save_dir,exist_ok=True)
        self.visualizer = Visualizer(model_type=self.model_type,resolution =vis_size, input_size=self.input_size, result_img_dir = test_save_dir,with_renderer=True)

        with torch.no_grad():
            for test_iter,data_3d in enumerate(loader_val):
                outputs, centermaps, heatmap_AEs, data_3d_new, reorganize_idx = self.net_forward(data_3d,self.generator,mode='test')
                if self.save_dict_results:
                    self.reorganize_results(outputs,data_3d['imgpath'],reorganize_idx,test_save_dir)
                if not self.save_centermap:
                    centermaps = None
                vis_eval_results = self.visualizer.visulize_result_onorg(outputs['verts'], outputs['verts_camed'], data_3d_new, reorganize_idx, centermaps=centermaps,save_img=True)#

                if self.save_mesh:
                    vids_org = np.unique(reorganize_idx)
                    for idx, vid in enumerate(vids_org):
                        verts_vids = np.where(reorganize_idx==vid)[0]
                        img_path = data_3d['imgpath'][verts_vids[0]]
                        obj_name = (test_save_dir+'/{}'.format(os.path.basename(img_path))).replace('.jpg','.obj').replace('.png','.obj')
                        for subject_idx, batch_idx in enumerate(verts_vids):
                            save_obj(outputs['verts'][batch_idx].detach().cpu().numpy().astype(np.float16), self.smplx.faces_tensor.detach().cpu().numpy(),obj_name.replace('.obj', '_{}.obj'.format(subject_idx)))
                if test_iter%50==0:
                    print(test_iter,'/',len(loader_val))

    def reorganize_results(self, outputs, img_paths, reorganize_idx,test_save_dir):
        results = {}
        cam_results = outputs['params']['cam'].detach().cpu().numpy().astype(np.float16)
        smpl_pose_results = torch.cat([outputs['params']['global_orient'], outputs['params']['body_pose']],1).detach().cpu().numpy().astype(np.float16)
        smpl_shape_results = outputs['params']['betas'].detach().cpu().numpy().astype(np.float16)
        kp3d_smpl24_results = outputs['j3d_smpl24'].detach().cpu().numpy().astype(np.float16)
        kp3d_op25_results = outputs['j3d_op25'].detach().cpu().numpy().astype(np.float16)
        verts_results = outputs['verts'].detach().cpu().numpy().astype(np.float16)

        vids_org = np.unique(reorganize_idx)
        for idx, vid in enumerate(vids_org):
            verts_vids = np.where(reorganize_idx==vid)[0]
            img_path = img_paths[verts_vids[0]]
            results[img_path] = [{} for idx in range(len(verts_vids))]
            for subject_idx, batch_idx in enumerate(verts_vids):
                results[img_path][subject_idx]['cam'] = cam_results[batch_idx]
                results[img_path][subject_idx]['pose'] = smpl_pose_results[batch_idx]
                results[img_path][subject_idx]['betas'] = smpl_shape_results[batch_idx]
                results[img_path][subject_idx]['j3d_smpl24'] = kp3d_smpl24_results[batch_idx]
                results[img_path][subject_idx]['j3d_op25'] = kp3d_op25_results[batch_idx]
                results[img_path][subject_idx]['verts'] = verts_results[batch_idx]

        for img_path, result_dict in results.items():
            name = (test_save_dir+'/{}'.format(os.path.basename(img_path))).replace('.jpg','.npz').replace('.png','.npz')
            # get the results: np.load('/path/to/person_overlap.npz',allow_pickle=True)['results'][()]
            np.savez(name, results=result_dict)

def main():
    demo = Demo()
    # run the code on demo images
    demo_image_folder = args.demo_image_folder
    if not os.path.exists(demo_image_folder):
        demo_image_folder = os.path.join(demo.demo_dir,'images')
    demo.run(demo_image_folder)


if __name__ == '__main__':
    main()